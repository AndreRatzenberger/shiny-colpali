import json

from byaldi import RAGMultiModalModel
from shiny import module, reactive, render, ui
from shiny.types import FileInfo


def input_group():
    return ui.div(
        ui.input_text("txt_query", "Input query", value=""),
        ui.input_action_button(
            "btn_query", "Query documents", width="100%", disabled=True
        ),
    )


def output_group():
    return ui.div(
        ui.output_text_verbatim("txt_status"),
        ui.output_ui("out_qry_results"),
    )


def create_accordion(name, image):
    return ui.accordion(
        ui.accordion_panel(
            f"{name}",
            ui.img({"src": f"data:image/png;base64,{image}", "width": "100%"}),
        ),
        open=False,
    )


@module.ui
def query_documents_ui():
    return ui.layout_sidebar(ui.sidebar(input_group(), width=350), output_group())


@module.server
def query_documents_server(input, output, session, processed_pdfs, rag_client):
    status_text = reactive.value("")
    query_result = reactive.value("")
    if processed_pdfs is None:
        processed_pdfs = reactive.value({})

    @reactive.effect
    def update_ui():
        rag = rag_client.get()

        if rag is not None:
            status_text.set(f"Index loaded...")
            ui.update_action_button("btn_query", disabled=False)
        else:
            status_text.set(f"Please build index first...")
            ui.update_action_button("btn_query", disabled=True)

    @reactive.effect
    @reactive.event(input.btn_query, ignore_none=True)
    def process_query():
        rag = rag_client.get()
        text_query = input.txt_query()
        results = rag.search(text_query, k=5)
        status_text.set(f"Query executed...")
        query_result.set(results)

    @render.text
    def txt_status():
        return status_text()

    @render.ui
    def out_qry_results():
        accordions = []
        results = query_result.get()
        pdfs = processed_pdfs.get()
        for doc in results:
            pdf = pdfs[doc.doc_id]  # type: ignore
            name = f"{pdf.name} - page {doc.page_num} - score {doc.score:.2f}"  # type: ignore
            accordions.append(create_accordion(name, doc.base64))  # type: ignore

        return ui.div(
            accordions,
            ui.HTML("<br>"),
        )
