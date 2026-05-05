---
layout: default
title: Blog
permalink: /Blog.html
---

### &emsp;&emsp; [ABOUT](./index.md)  &emsp; BLOG &emsp; [TEACHING](./Teaching.md) &emsp; [MENTORSHIP](./Mentorship.md) &emsp;

-------

# Blog
***Views are my own***
Notes on building 0->1 products, better metrics, trustworthy AI, and personalization, and the messy middle between research and shipped product. Occassionally you might find notes about women empowerment, education, environment, policy, books I have been reading, and everthing in between!

<ul style="list-style-type: none; padding: 0;">
{% for post in site.posts %}
  <li style="margin-bottom: 1.2em;">
    <a href="{{ post.url | relative_url }}" style="font-size: 1.1em; font-weight: 600;">{{ post.title }}</a>
    <div style="color: #666; font-size: 0.9em;">{{ post.date | date: "%B %d, %Y" }}</div>
    {% if post.excerpt %}
      <div style="margin-top: 0.4em;">{{ post.excerpt | strip_html | truncate: 200 }}</div>
    {% endif %}
  </li>
{% endfor %}
</ul>

{% if site.posts.size == 0 %}
*No posts yet — first one coming soon.*
{% endif %}
