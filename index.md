---
layout: default
title: "Elon Musk Book Recommendations"
---

<h1>📚 Elon Musk Book Recommendations</h1>

<p>Books recommended by Elon Musk, with his original comments and links to the source on X/Twitter.</p>

<link rel="stylesheet" href="/assets/style.css">

<div class="book-grid">
{% for book in site.books %}
  {% include book-card.html book=book %}
{% endfor %}
</div>
