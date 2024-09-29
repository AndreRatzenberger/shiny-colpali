import shinyswatch
from shiny import App, reactive, ui

from modules.import_documents import (
    import_documents_server,
    import_documents_ui,
)
from modules.query_documents import (
    query_documents_server,
    query_documents_ui,
)


def placeholder(text=""):
    """Placeholder ui module"""
    return ui.div(
        f"nice! {text}",
        style="font-weight: bold; font-size: 18px; text-align: center;",
    )


def app_ui():
    return ui.page_sidebar(
        ui.sidebar(shinyswatch.theme_picker_ui(), open="closed"),
        ui.page_navbar(
            ui.nav_panel(
                "1. Import Documents", import_documents_ui("import_documents")
            ),
            ui.nav_panel("2. Query documents", query_documents_ui("query_documents")),
            title="# ColPali # ",
        ),
        theme=shinyswatch.theme.sandstone,
    )


def app_server(input, output, session):
    processed_pdfs = reactive.value([])
    rag_client = reactive.value(None)
    shinyswatch.theme_picker_server()
    import_documents_server("import_documents", processed_pdfs, rag_client)
    query_documents_server("query_documents", processed_pdfs, rag_client)


app = App(app_ui(), app_server)
