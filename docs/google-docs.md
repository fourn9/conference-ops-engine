# Speaker prospectus automation

The source-derived `fill_prospectus.py` copies a Google Doc and fills five body sections, then converts bullet markers and replaces the company/name title tokens. The script uses `gcloud` and `curl`; it does not include account configuration.

Create your own Google Doc from [the text template](../templates/prospectus-document.md). Use ordinary body paragraphs (not tables). Keep each heading followed by a separate `〇〇` paragraph, and keep the title tokens `株式会社〇〇` and `〇〇様`. The script locates body paragraphs by heading and will fail if a section has no placeholder before the next heading.

Prepare content with the keys in [prospectus-content.json](../examples/prospectus-content.json). Put real content in `local/`. A preview makes no API or token calls:

```sh
python3 .claude/skills/speaker-prospectus/fill_prospectus.py --from-template YOUR_TEMPLATE_DOC_ID --company 'サンプル株式会社' --name 'サンプル太郎' --content examples/prospectus-content.json
```

For a real write, configure your own Google account with access to the document and Drive/Docs API permissions, replace the ID and content, and add `--apply`. `--from-template` copies the document to its template's parent folder; `--doc` edits an existing document directly. The script does not change sharing permissions. Writes are sequential API requests, not an atomic transaction: inspect the copied document after any failure before retrying.

Sections are replaced in descending document-index order while keeping paragraph terminators. Native bullets are created before marker deletion. Title replacement happens last, after index-sensitive body edits. The result is fetched again to check remaining `〇` placeholders; a remaining placeholder exits with code 2. Offline tests verify ordering, section boundaries, and preview behavior; they do not exercise a live Google account.
