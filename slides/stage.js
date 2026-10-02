(function () {
  var API = location.origin;
  var term = null;
  var es = null;
  var filePath = "";
  var abortCtl = null;
  var running = false;

  var ide = document.getElementById("wid-ide");
  var gh = document.getElementById("wid-gh");
  var xtermEl = document.getElementById("xterm");
  var idePath = document.getElementById("ide-path");
  var ideLn = document.getElementById("ide-ln");
  var ideCode = document.getElementById("ide-code");
  var filesEl = document.getElementById("ide-files");
  var ghLog = document.getElementById("gh-live-log");
  var ghStatus = document.getElementById("gh-live-status");
  var ghMsg = document.getElementById("gh-live-msg");
  var ghBtn = document.getElementById("gh-live-btn");
  var ghRun = document.getElementById("gh-live-run");
  var ghCode = document.getElementById("gh-code");
  var ghActions = document.getElementById("gh-actions");
  var ghUrl = document.getElementById("gh-url");
  var ghCodeBody = document.getElementById("gh-code-body");

  function paint(line) {
    var t = String(line).replace(/&/g, "&amp;").replace(/</g, "&lt;");
    var cls = /\bFailed\b/.test(t) ? "fail" : /\bPassed\b/.test(t) ? "ok" : "";
    return cls ? '<div class="ln ' + cls + '">' + t + "</div>" : '<div class="ln">' + t + "</div>";
  }
  function append(el, line) {
    el.insertAdjacentHTML("beforeend", paint(line));
    el.scrollTop = el.scrollHeight;
  }

  function ensureTerm() {
    if (term || !window.Terminal || !xtermEl) return;
    term = new Terminal({
      cursorBlink: true,
      fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
      fontSize: 13,
      theme: {
        background: "#0c1713",
        foreground: "#fff4ec",
        cursor: "#1fa9c4",
        selectionBackground: "#6a00bb"
      },
      convertEol: true
    });
    term.open(xtermEl);
    term.onData(function (d) {
      fetch(API + "/api/pty", { method: "POST", body: d, cache: "no-store" }).catch(function () {});
    });
  }

  function attachPty() {
    ensureTerm();
    if (es) { try { es.close(); } catch (e) {} }
    fetch(API + "/api/pty/start", { method: "POST" }).catch(function () {});
    es = new EventSource(API + "/api/pty");
    es.onmessage = function (ev) {
      var msg;
      try { msg = JSON.parse(ev.data); } catch (err) { return; }
      if (msg.t && term) term.write(msg.t);
    };
  }

  function loadFile(path) {
    path = path || filePath || "catalog/views.py";
    filePath = path;
    if (idePath) idePath.textContent = path;
    fetch(API + "/api/file?path=" + encodeURIComponent(path))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var text = d.text || "";
        var lines = text.split("\n");
        if (lines[lines.length - 1] === "") lines.pop();
        if (ideLn) ideLn.innerHTML = lines.map(function (_, n) { return n + 1; }).join("<br>");
        if (ideCode) ideCode.textContent = lines.join("\n");
        if (ghCodeBody) ghCodeBody.textContent = text;
      })
      .catch(function () {});
  }

  function loadTree() {
    fetch(API + "/api/tree")
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var files = d.files || [];
        if (filesEl) {
          filesEl.innerHTML = files.map(function (f) {
            return '<button type="button" class="ide-file" data-path="' + f + '">' + f + "</button>";
          }).join("");
        }
        var list = document.getElementById("gh-file-list");
        if (list) {
          list.innerHTML = files.map(function (f) {
            return '<button type="button" class="gh-file" data-path="' + f + '">' + f + "</button>";
          }).join("");
        }
      })
      .catch(function () {});
  }

  function openIde() {
    gh.classList.remove("open");
    ide.classList.add("open");
    loadTree();
    var sl = window.TalkDeck && TalkDeck.current ? TalkDeck.current() : null;
    loadFile((sl && (sl.dataset.open || sl.dataset.git)) || "catalog/views.py");
    attachPty();
    setTimeout(function () { if (term) term.focus(); }, 80);
  }
  function openGh(tab) {
    ide.classList.remove("open");
    gh.classList.add("open");
    loadTree();
    setGhTab(tab || "actions");
  }
  function closeAll() {
    ide.classList.remove("open");
    gh.classList.remove("open");
  }
  function anyOpen() {
    return ide.classList.contains("open") || gh.classList.contains("open");
  }

  function setGhTab(tab) {
    document.querySelectorAll(".gh-nav [data-tab]").forEach(function (el) {
      el.classList.toggle("on", el.dataset.tab === tab);
    });
    if (ghCode) ghCode.classList.toggle("on", tab === "code");
    if (ghActions) ghActions.classList.toggle("on", tab === "actions");
    if (ghUrl) {
      ghUrl.textContent = tab === "code"
        ? "github.com/mabukhashabeh/django-day-cph-2026"
        : "github.com/mabukhashabeh/django-day-cph-2026/actions";
    }
    if (tab === "code") loadFile(filePath || ".pre-commit-config.yaml");
  }

  function runActions() {
    if (abortCtl) { try { abortCtl.abort(); } catch (e) {} }
    running = true;
    setGhTab("actions");
    ghLog.innerHTML = '<div class="ln dim">$ pre-commit run --all-files</div>';
    ghStatus.textContent = "In progress";
    ghStatus.className = "gh-status st-run";
    ghMsg.textContent = "Checks running…";
    ghBtn.disabled = true;
    ghBtn.classList.remove("go");
    abortCtl = new AbortController();
    fetch(API + "/api/run?id=all-files", { signal: abortCtl.signal, cache: "no-store" })
      .then(function (r) {
        if (!r.body) throw new Error("no stream");
        var reader = r.body.getReader();
        var dec = new TextDecoder();
        var buf = "";
        function pump() {
          return reader.read().then(function (chunk) {
            if (chunk.done) {
              if (running) finishActions(1);
              return;
            }
            buf += dec.decode(chunk.value, { stream: true });
            var parts = buf.split("\n\n");
            buf = parts.pop();
            parts.forEach(function (block) {
              var line = block.split("\n").filter(function (l) { return l.indexOf("data: ") === 0; })
                .map(function (l) { return l.slice(6); }).join("");
              if (!line) return;
              var msg;
              try { msg = JSON.parse(line); } catch (err) { return; }
              if (msg.kind === "line") append(ghLog, msg.text);
              if (msg.kind === "exit") finishActions(msg.code);
            });
            if (running) return pump();
          });
        }
        return pump();
      })
      .catch(function (err) {
        if (!running || (err && err.name === "AbortError")) return;
        append(ghLog, "Could not reach the presenter. Run: python3.12 scripts/present.py");
        finishActions(1);
      });
  }

  function finishActions(code) {
    running = false;
    var ok = code === 0;
    append(ghLog, ok ? "exit 0" : "exit " + code);
    ghStatus.textContent = ok ? "Passed" : "Failed";
    ghStatus.className = "gh-status " + (ok ? "st-pass" : "st-fail");
    ghMsg.textContent = ok ? "All checks have passed." : "Merging is blocked. A required check is failing.";
    ghBtn.disabled = !ok;
    ghBtn.classList.toggle("go", ok);
    var fail = ghLog.querySelector(".fail");
    if (fail) fail.scrollIntoView({ block: "center", inline: "nearest" });
  }

  document.getElementById("ide-close").addEventListener("click", closeAll);
  document.getElementById("gh-close").addEventListener("click", closeAll);
  ghRun.addEventListener("click", runActions);

  document.addEventListener("click", function (e) {
    var fileBtn = e.target.closest("[data-path]");
    if (fileBtn) {
      loadFile(fileBtn.getAttribute("data-path"));
      if (e.target.closest("#gh-file-list")) setGhTab("code");
    }
    var tab = e.target.closest(".gh-nav [data-tab]");
    if (tab) setGhTab(tab.dataset.tab);
  });

  document.addEventListener("keydown", function (e) {
    var helpEl = document.getElementById("help");
    if (helpEl && helpEl.classList.contains("show")) return;
    if (e.target && (e.target.closest(".xterm") || e.target.closest("#wid-ide") || e.target.closest("#wid-gh"))) {
      if (e.key === "Escape") { closeAll(); e.stopPropagation(); }
      return;
    }
    var k = e.key;
    if (k === "t" || k === "T") { e.preventDefault(); e.stopPropagation(); if (ide.classList.contains("open")) closeAll(); else openIde(); }
    else if (k === "g" || k === "G") {
      if (e.shiftKey) return;
      e.preventDefault();
      e.stopPropagation();
      if (gh.classList.contains("open")) closeAll();
      else openGh("actions");
    } else if (k === "Escape" && anyOpen()) {
      e.preventDefault();
      e.stopPropagation();
      closeAll();
    }
  }, true);

  if (window.TalkDeck) {
    TalkDeck.toggleActions = function () { if (gh.classList.contains("open")) closeAll(); else openGh("actions"); };
    TalkDeck.toggleMachine = function () { if (ide.classList.contains("open")) closeAll(); else openIde(); };
    TalkDeck.onShow(function (sl) {
      if (ide.classList.contains("open") && sl) {
        loadFile(sl.dataset.open || sl.dataset.git || filePath);
      }
    });
  }
})();
