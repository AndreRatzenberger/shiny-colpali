from byaldi import RAGMultiModalModel
from shiny import module, reactive, render, ui
from shiny.types import FileInfo


def input_group():
    return ui.div(
        ui.output_text_verbatim("txt_status"),
        ui.input_action_button(
            "btn_process_pdfs", "Process PDFs", width="100%", disabled=True
        ),
    )


def output_group():
    return ui.div()


@module.ui
def process_documents_ui():
    return ui.layout_sidebar(ui.sidebar(input_group(), width=350), output_group())


@module.server
def process_documents_server(input, output, session, processed_pdfs, rag_client):
    status_text = reactive.value("")
    if processed_pdfs is None:
        processed_pdfs = reactive.value({})

    @reactive.effect
    def update_ui():
        status_text.set(f"{len(processed_pdfs.get())} pdfs loaded...")
        ui.update_action_button(
            "btn_process_pdfs", disabled=(len(processed_pdfs.get()) == 0)
        )

    @reactive.effect
    @reactive.event(input.btn_process_pdfs, ignore_none=True)
    def process_pdfs():
        status_text.set("Processing PDFs...")
        document_list = processed_pdfs.get()
        RAG = RAGMultiModalModel.from_pretrained("vidore/colpali")
        with ui.Progress(min=0, max=len(document_list)) as p:
            p.set(message="Indexing files", detail="This may take a while...")
            i = 0
            for docs in document_list:
                i += 1
                p.set(i, message="Indexing files", detail=docs.name)
                RAG.index(
                    input_path=docs.path,
                    index_name="image_index",  # index will be saved at index_root/index_name/
                    store_collection_with_index=True,
                    overwrite=True,
                )
        rag_client.set(RAG)

    @render.text
    def txt_status():
        return status_text()
