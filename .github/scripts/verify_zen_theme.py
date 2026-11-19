"""Opt-in integration check against the installed Zen, using disposable profiles.

Run locally, not as part of the generic CI image. Never opens a real user profile.
Marionette/system access is enabled only in the isolated test process.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def execute_template(text):
    return subprocess.run(
        ["chezmoi", "execute-template", "--source", str(ROOT), "--config", "/dev/null",
         "--config-format", "toml"], input=text,
        text=True, capture_output=True, check=True).stdout


def render(source):
    return execute_template((ROOT / source).read_text())


def rgb(color):
    return "rgb(" + ", ".join(str(int(color[index:index + 2], 16)) for index in (1, 3, 5)) + ")"


class Marionette:
    def __init__(self, connection):
        self.socket = connection
        self.number = 0
        self.receive()

    def receive(self):
        length = b""
        while (char := self.socket.recv(1)) != b":":
            if not char:
                raise EOFError("Marionette disconnected")
            length += char
        remaining = int(length)
        data = b""
        while remaining:
            chunk = self.socket.recv(remaining)
            if not chunk:
                raise EOFError("Incomplete Marionette response")
            data += chunk
            remaining -= len(chunk)
        return json.loads(data)

    def call(self, command, parameters=None):
        self.number += 1
        data = json.dumps([0, self.number, command, parameters or {}]).encode()
        self.socket.sendall(str(len(data)).encode() + b":" + data)
        response = self.receive()
        if response[0:2] != [1, self.number] or response[2]:
            raise RuntimeError(response)
        return response[3]

    def script(self, source, asynchronous=False):
        command = "WebDriver:ExecuteAsyncScript" if asynchronous else "WebDriver:ExecuteScript"
        result = self.call(command, {
            "script": source, "args": [], "newSandbox": True,
            "sandbox": "default", "filename": "zen-theme-check", "line": 1,
        })
        return result.get("value", result) if isinstance(result, dict) else result


def verify(container, profile, directory, theme):
    directory.mkdir(parents=True, exist_ok=True)
    chrome = {name: render(f"dot_zen/{profile}/chrome/{name}.tmpl")
              for name in ("userChrome.css", "userContent.css")}
    prefs = render(f"dot_zen/{profile}/user.js.tmpl")
    # Use a new directory on every run so preferences/addons cannot mask regressions.
    import tempfile
    browser_profile = Path(tempfile.mkdtemp(prefix=profile + "-", dir=directory))
    (browser_profile / "chrome").mkdir()
    for name, text in chrome.items():
        (browser_profile / "chrome" / name).write_text(text)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    test_prefs = {
        "marionette.port": port, "browser.startup.page": 0,
        "browser.startup.homepage": "about:blank",
        "browser.aboutwelcome.enabled": False,
        "browser.shell.checkDefaultBrowser": False,
        "zen.welcome-screen.seen": True,
        "app.update.enabled": False, "app.normandy.enabled": False,
        "extensions.update.enabled": False,
        "datareporting.policy.dataSubmissionEnabled": False,
        "layout.css.report_errors": True,
    }
    prefs += "\n" + "\n".join(
        f"user_pref({json.dumps(key)}, {json.dumps(value)});"
        for key, value in test_prefs.items())
    (browser_profile / "user.js").write_text(prefs)
    home = browser_profile / "test-home"
    home.mkdir()
    pid_file = browser_profile / "browser.pid"
    user = f"{os.getuid()}:{os.getgid()}"
    command = ["podman", "exec", "--user", user,
               "-e", f"HOME={home}", "-e", f"XDG_CACHE_HOME={home / '.cache'}",
               "-e", f"XDG_CONFIG_HOME={home / '.config'}",
               "-e", "MOZ_ENABLE_WAYLAND=0",
               "-e", "DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent",
               container, "/bin/sh", "-c", 'echo $$ > "$1"; shift; exec "$@"', "zen-test",
               str(pid_file), "/opt/zen/zen-bin", "--headless", "--no-remote",
               "--profile", str(browser_profile), "--marionette",
               "--remote-allow-system-access", "about:blank"]
    client = None
    owns_browser = False
    report = {}
    with (directory / f"{profile}.log").open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 45
            while True:
                try:
                    connection = socket.create_connection(("127.0.0.1", port), timeout=2)
                    connection.settimeout(30)
                    client = Marionette(connection)
                    break
                except (ConnectionRefusedError, TimeoutError):
                    if process.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError(f"Zen did not start; see {profile}.log")
                    time.sleep(0.2)
            report["session"] = client.call("WebDriver:NewSession", {
                "capabilities": {"alwaysMatch": {"pageLoadStrategy": "normal"}}})
            actual_profile = report["session"]["capabilities"]["moz:profile"]
            if Path(actual_profile).resolve() != browser_profile.resolve():
                raise RuntimeError("Refusing to automate an unrelated browser profile")
            owns_browser = True
            client.call("Marionette:SetContext", {"value": "chrome"})
            report["chrome"] = client.script("""
                const root = document.documentElement;
                const style = getComputedStyle(root);
                const oldScheme = root.getAttribute("zen-should-be-dark-mode");
                root.setAttribute("zen-should-be-dark-mode", "false");
                const schemeWithLightWorkspace = getComputedStyle(document.getElementById("browser")).colorScheme;
                if (oldScheme === null) root.removeAttribute("zen-should-be-dark-mode");
                else root.setAttribute("zen-should-be-dark-mode", oldScheme);
                const read = selector => {
                    const element = document.querySelector(selector);
                    if (!element) return null;
                    const s = getComputedStyle(element);
                    return {background: s.backgroundColor, color: s.color,
                            font: s.fontFamily, weight: s.fontWeight, shadow: s.boxShadow};
                };
                return {
                    url: document.URL,
                    dark: matchMedia("(prefers-color-scheme: dark)").matches,
                    schemeWithLightWorkspace,
                    accent: style.getPropertyValue("--nord-profile-accent").trim(),
                    toolbox: read("#navigator-toolbox"),
                    outerFrame: read("#zen-browser-background"),
                    contentFrame: read("#tabbrowser-tabpanels browser[type='content']"),
                    address: read("#urlbar-input"),
                    selectedTab: read(".tabbrowser-tab[selected] .tab-background"),
                    workspace: read(".zen-current-workspace-indicator-name"),
                    parserChecked: typeof Services !== "undefined",
                    parserErrors: typeof Services !== "undefined" ?
                        Services.console.getMessageArray()
                            .filter(m => m.sourceName?.includes("/chrome/user") &&
                                         m.category === "CSS Parser")
                            .map(m => ({message: m.errorMessage, line: m.lineNumber})) : []
                };
            """)
            assert report["chrome"]["toolbox"]["background"] == rgb(theme["palette"]["nord2"]), report
            assert report["chrome"]["outerFrame"]["background"] == rgb(theme["palette"]["nord2"]), report
            assert report["chrome"]["contentFrame"]["background"] == rgb(theme["palette"]["nord3"]), report
            assert report["chrome"]["dark"], report
            assert report["chrome"]["schemeWithLightWorkspace"] == "dark", report
            assert theme["fonts"]["mono"] in report["chrome"]["address"]["font"], report
            expected = theme["palette"][theme["profiles"][profile]["accent"]]
            assert report["chrome"]["accent"] == expected, report
            assert theme["fonts"]["display"] in report["chrome"]["workspace"]["font"], report
            assert report["chrome"]["workspace"]["weight"] == str(theme["fonts"]["display_weight"]), report
            assert report["chrome"]["parserChecked"], report
            assert not report["chrome"]["parserErrors"], report
            fonts = [theme["fonts"][role] for role in ("sans", "mono", "display")]
            report["fonts"] = client.script("return " + json.dumps(fonts) + """.map(name => {
                    const probe = document.createElementNS("http://www.w3.org/1999/xhtml", "span");
                    probe.textContent = "Nord 0123 Aa";
                    probe.style.cssText = 'position:fixed;top:-100px;font-family:"' + name + '"';
                    document.documentElement.append(probe);
                    probe.getBoundingClientRect();
                    const range = document.createRange();
                    range.selectNodeContents(probe);
                    const faces = Array.from(window.InspectorUtils.getUsedFontFaces(range))
                        .map(face => ({family: face.CSSFamilyName, name: face.name}));
                    probe.remove();
                    return {name, faces, loaded: faces.some(face => face.family === name)};
                });
            """)
            assert all(font["loaded"] for font in report["fonts"]), report
            screenshot = client.call("WebDriver:TakeScreenshot", {})
            if isinstance(screenshot, dict):
                screenshot = screenshot["value"]
            (directory / f"{profile}-chrome.png").write_bytes(base64.b64decode(screenshot))
            report["menu"] = client.script("""
                const done = arguments[arguments.length - 1];
                Promise.resolve(window.PanelUI.show()).then(() => {
                    const panel = window.PanelUI.panel;
                    const deadline = Date.now() + 5000;
                    const ready = () => {
                        if (panel.state === "open" || Date.now() > deadline) {
                            const s = getComputedStyle(panel);
                            done({state: panel.state, background: s.backgroundColor, color: s.color});
                        } else setTimeout(ready, 100);
                    };
                    ready();
                });
            """, asynchronous=True)
            assert report["menu"]["state"] == "open", report
            assert report["menu"]["background"] == rgb(theme["palette"]["nord2"]), report
            client.script("window.PanelUI.panel.hidePopup();")
            client.call("Marionette:SetContext", {"value": "content"})
            client.call("WebDriver:Navigate", {"url": "about:preferences"})
            client.script("""
                const done = arguments[arguments.length - 1];
                const deadline = Date.now() + 10000;
                const ready = () => {
                    if (document.querySelector("h1, h2, .header-name") || Date.now() > deadline)
                        done(true);
                    else setTimeout(ready, 100);
                };
                ready();
            """, asynchronous=True)
            report["preferences"] = client.script("""
                const body = getComputedStyle(document.body);
                const heading = document.querySelector("h1, h2, .header-name");
                return {background: body.backgroundColor, color: body.color,
                        font: body.fontFamily,
                        headingFont: heading ? getComputedStyle(heading).fontFamily : null,
                        url: location.href,
                        dark: matchMedia("(prefers-color-scheme: dark)").matches};
            """)
            assert report["preferences"]["background"] == rgb(theme["palette"]["nord3"]), report
            assert theme["fonts"]["display"] in report["preferences"]["headingFont"], report
            screenshot = client.call("WebDriver:TakeScreenshot", {})
            if isinstance(screenshot, dict):
                screenshot = screenshot["value"]
            (directory / f"{profile}-preferences.png").write_bytes(base64.b64decode(screenshot))
            for page in ("about:addons", "about:newtab"):
                client.call("WebDriver:Navigate", {"url": page})
                report[page] = client.script("""
                    const s = getComputedStyle(document.body || document.documentElement);
                    return {background: s.backgroundColor, color: s.color, font: s.fontFamily};
                """)
                assert report[page]["background"] == rgb(theme["palette"]["nord3"]), report
            client.call("WebDriver:Navigate", {"url":
                "data:text/html,<style>body{background:rgb(250,249,248);color:rgb(20,21,22);font-family:serif}</style><p>Website styles stay intact</p>"})
            report["website"] = client.script("""
                const s = getComputedStyle(document.body);
                return {background: s.backgroundColor, color: s.color, font: s.fontFamily,
                        leakedToken: s.getPropertyValue("--nord-base"),
                        dark: matchMedia("(prefers-color-scheme: dark)").matches};
            """)
            assert report["website"]["background"] == "rgb(250, 249, 248)", report
            assert report["website"]["color"] == "rgb(20, 21, 22)", report
            assert report["website"]["font"] == "serif", report
            assert not report["website"]["leakedToken"], report
            assert report["website"]["dark"], report
            report["websiteFrames"] = client.script("""
                const done = arguments[arguments.length - 1];
                const html = '<style>body{background:rgb(250,249,248);font-family:serif}</style><p>Frame</p>';
                Promise.all(["blank", "srcdoc"].map(mode => new Promise(resolve => {
                    const frame = document.createElement("iframe");
                    const read = () => {
                        const s = frame.contentWindow.getComputedStyle(frame.contentDocument.body);
                        resolve({mode, background: s.backgroundColor, font: s.fontFamily,
                                 leakedToken: s.getPropertyValue("--nord-base")});
                    };
                    if (mode === "srcdoc") {
                        frame.onload = read;
                        frame.srcdoc = html;
                        document.body.append(frame);
                    } else {
                        document.body.append(frame);
                        frame.contentDocument.open();
                        frame.contentDocument.write(html);
                        frame.contentDocument.close();
                        read();
                    }
                }))).then(done);
            """, asynchronous=True)
            for frame in report["websiteFrames"]:
                assert frame["background"] == "rgb(250, 249, 248)", report
                assert frame["font"] == "serif" and not frame["leakedToken"], report
            print(f"{profile}: chrome, fonts, internal pages and website isolation PASS")
        finally:
            (directory / f"{profile}.json").write_text(json.dumps(report, indent=2) + "\n")
            if client and owns_browser:
                try:
                    client.call("Marionette:Quit", {"flags": ["eForceQuit"]})
                except (OSError, EOFError, RuntimeError):
                    pass
            if client:
                client.socket.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Match the disposable profile before signaling any PID.
                subprocess.run(["podman", "exec", "--user", user, container, "python3", "-c",
                                "import os,sys,signal,pathlib; p=int(pathlib.Path(sys.argv[1]).read_text()); "
                                "c=pathlib.Path(f'/proc/{p}/cmdline'); "
                                "os.kill(p,signal.SIGTERM) if c.exists() and sys.argv[2].encode() in c.read_bytes().split(b'\\0') else None",
                                str(pid_file), str(browser_profile)], check=True)
                process.wait(timeout=10)
            # Firefox leaves a dangling lock symlink even after a clean quit;
            # keep screenshots/reports, not disposable profiles in chezmoi's source.
            shutil.rmtree(browser_profile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", default="zen-distrobox")
    args = parser.parse_args()
    data = json.loads(execute_template("{{ .zen | toJson }}"))
    for name in data["profiles"]:
        verify(args.container, name, ROOT / ".build/zen-theme", data)
