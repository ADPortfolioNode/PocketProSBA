(function () {
  "use strict";
  var PAGES = [
    { href: "index.html", label: "Home" },
    { href: "demo.html", label: "Demo" },
    { href: "features.html", label: "Features" },
    { href: "how-it-works.html", label: "How it works" },
    { href: "docs.html", label: "Docs" },
    { href: "pricing.html", label: "Pricing" },
    { href: "about.html", label: "About" },
    { href: "contact.html", label: "Contact" }
  ];
  function fileName() {
    var path = (window.location.pathname || "/").split("/").pop();
    return path && path.length ? path : "index.html";
  }
  function navHtml() {
    var current = fileName();
    var links = PAGES.map(function (page) {
      var active = page.href === current ? ' aria-current="page"' : "";
      return '<a href="' + page.href + '"' + active + ">" + page.label + "</a>";
    }).join("");
    return '<header class="site-header"><div class="site-header__inner"><a class="brand" href="index.html">Pocket<span>Pro</span>SBA</a><button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu"></button><nav class="site-nav" id="site-nav">' + links + "</nav></div></header>";
  }
  function footerHtml() {
    return '<footer class="site-footer"><div class="site-footer__inner"><a class="brand" href="index.html" style="color:#fbf7f0">Pocket<span>Pro</span>SBA</a><p>Self-hosted SBA RAG for small-business funding guidance. Official program details always belong to sba.gov.</p></div></footer>';
  }
  var headerMount = document.querySelector("[data-nav]");
  var footerMount = document.querySelector("[data-footer]");
  if (headerMount) headerMount.innerHTML = navHtml();
  if (footerMount) footerMount.innerHTML = footerHtml();
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
})();
