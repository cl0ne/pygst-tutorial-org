function ready(callback) {
    if (document.readyState != "loading") callback();
    else document.addEventListener("DOMContentLoaded", callback);
}

ready(function () {
    document.querySelectorAll("pre.src-sh").forEach(function (e) {
        var lines = e.textContent.split("\n");
        for (var i = 0; i < lines.length; ++i) {
            var text = lines[i];
            if (!text || (text[0] == " ") | (text[0] == "\t")) {
                continue;
            }
            lines[i] = '<span class="shell-line"></span>' + text;
        }
        e.innerHTML = lines.join("\n");
    });

    // broken way to do things for now.
    var footer = document.querySelector("div.status");
    var sourceBlock = document.createElement("p");
    var sourceLink = document.createElement("a");
    sourceLink.href = "index.org";
    sourceLink.textContent = "org source";
    sourceBlock.appendChild(sourceLink);
    footer.insertBefore(sourceBlock, footer.children[0]);
    footer.insertBefore(document.createElement("hr"), sourceBlock);
});
