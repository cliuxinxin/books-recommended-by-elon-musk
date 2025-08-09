---
layout: default
title: "Elon Musk Book Recommendations"
---

<link rel="stylesheet" href="{{ site.baseurl }}/assets/style.css">

<div class="container">
  <div class="hero">
    <h1>📚 Elon Musk Book Recommendations</h1>
    <p>Curated list of books Elon Musk has recommended. Each card includes his quote and the original source.</p>
  </div>

  <div class="book-grid">
  {% assign sorted_books = site.books | sort: 'title' %}
  {% for book in sorted_books %}
    {% include book-card.html book=book %}
  {% endfor %}
  </div>
</div>
