"""Dependency-free HTML profile generation from the frozen frame manifest."""

from __future__ import annotations

from collections import Counter
from html import escape
from pathlib import Path

from discern.data.manifest import Stage1Manifest


def _table(title: str, values: Counter[str]) -> str:
    rows = "".join(
        f"<tr><td>{escape(str(name))}</td><td>{count}</td></tr>"
        for name, count in sorted(values.items())
    )
    return (
        f"<section><h2>{escape(title)}</h2><table>"
        "<thead><tr><th>Value</th><th>Count</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></section>"
    )


def write_data_profile(manifest: Stage1Manifest, output_path: Path) -> Path:
    """Render traceable counts without loading raw sensor payloads."""
    subsets: Counter[str] = Counter(frame.subset for frame in manifest.frames)
    objects: Counter[str] = Counter()
    distances: Counter[str] = Counter()
    scene_tags: Counter[str] = Counter()
    missing: Counter[str] = Counter()
    for frame in manifest.frames:
        objects.update(frame.object_counts)
        distances.update(frame.distance_counts)
        scene_tags.update(frame.scene_tags)
        missing.update(frame.missing_channels)

    body = "".join(
        (
            _table("Frames by subset", subsets),
            _table("Objects by class", objects),
            _table("Objects by distance band (m)", distances),
            _table("Scene tags", scene_tags),
            _table("Missing sensor frames", missing),
        )
    )
    content = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>DISCERN-AV Stage 1 data profile</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 20px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccc;padding:6px}}
th{{text-align:left;background:#f3f3f3}}code{{overflow-wrap:anywhere}}
</style></head><body>
<h1>DISCERN-AV Stage 1 data profile</h1>
<p>Dataset: {escape(manifest.dataset)} {escape(manifest.dataset_version)}</p>
<p>Manifest SHA-256: <code>{manifest.content_hash()}</code></p>
<p>Scenes: {len(manifest.scenes)} · Frames: {len(manifest.frames)}</p>
{body}</body></html>
"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path
