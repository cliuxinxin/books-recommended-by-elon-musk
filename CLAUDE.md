# CLAUDE.md

使用中文

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
A Jekyll-based static site that catalogs books recommended by Elon Musk, featuring his original quotes and links to the source tweets.

## Architecture
- **Static site generator**: Jekyll with minima theme
- **Content structure**: Uses Jekyll collections for books (`site.books`)
- **URLs**: `/books/:name` for individual book pages
- **Assets**: Images in `/assets/cover/` directory
- **Templates**: Custom layouts in `_layouts/` and includes in `_includes/`

## Key Files
- `_config.yml`: Jekyll configuration with collections setup
- `books/*.md`: Individual book entries with frontmatter
- `index.md`: Homepage showing book grid
- `_includes/book-card.html`: Book card component for grid display
- `_layouts/book.html`: Individual book page layout
- `assets/style.css`: Custom styling

## Development Commands
```bash
# Serve locally (requires Jekyll)
bundle exec jekyll serve

# Build for production
bundle exec jekyll build

# Add a new book
# 1. Create books/[slug].md with frontmatter
# 2. Add cover image to assets/cover/[slug].png
# 3. Required frontmatter: title, author, year, quote, source, summary, cover
```

## Content Format
Each book file uses YAML frontmatter:
```yaml
---
title: "Book Title"
author: "Author Name"
year: 2024
quote: "Musk's comment"
source: "https://x.com/elonmusk/status/..."
summary: "Book description"
cover: "/assets/cover/file-name.jpg"
---
```