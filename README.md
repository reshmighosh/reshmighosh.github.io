
#Personal Website

Personal Website set up using minimal mistakes theme on Github pages from scratch.

## Blog post layout

Posts use a compact header with navigation, profile links, and email, followed by
a centered reading column up to 760px wide. Standalone figures and tables can use
the wider 1200px page container; wide tables support horizontal keyboard scrolling
on small screens. These styles apply only to the `posts` collection, leaving the
homepage, blog index, and other pages in their existing sidebar layout.

Profile destinations and the contact email are configured in `_config.yml`.
The shared links are rendered by `_includes/profile-links.html`; the post-only
styles and table enhancement live in `assets/css/posts.css` and
`assets/js/post-layout.js`.
