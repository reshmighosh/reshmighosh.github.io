document.querySelectorAll(".post-content > table").forEach((table, index) => {
  const region = document.createElement("div");
  const caption = table.querySelector("caption");
  region.className = "post-table";
  region.tabIndex = 0;
  region.setAttribute("role", "region");
  region.setAttribute(
    "aria-label",
    caption
      ? caption.textContent.trim()
      : `Article table ${index + 1}; scroll horizontally if needed`
  );
  table.before(region);
  region.append(table);
});
