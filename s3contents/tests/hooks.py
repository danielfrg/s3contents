import os

import nbformat


def scrub_output_pre_save(model, **kwargs):
    """scrub output before saving notebooks"""
    # only run on notebooks
    if model["type"] != "notebook":
        return
    # only run on nbformat v4
    if model["content"]["nbformat"] != 4:
        return

    for cell in model["content"]["cells"]:
        if cell["cell_type"] != "code":
            continue
        cell["outputs"] = []
        cell["execution_count"] = None


def make_html_post_save(model, s3_path, contents_manager, **kwargs):
    """
    convert notebooks to HTML after saving via nbconvert
    """
    from nbconvert import HTMLExporter

    if model["type"] != "notebook":
        return

    content, _format = contents_manager.fs.read(s3_path, format="text")
    my_notebook = nbformat.reads(content, as_version=4)

    html_exporter = HTMLExporter()
    html_exporter.template_name = "classic"

    (body, resources) = html_exporter.from_notebook_node(my_notebook)

    base, ext = os.path.splitext(s3_path)
    contents_manager.fs.write(path=(base + ".html"), content=body, format=_format)
