import base64
from io import BytesIO

from byaldi import RAGMultiModalModel
from loguru import logger
from pdf2image import convert_from_path
from shiny import module, reactive, render, ui
from shiny.types import FileInfo

from core.logging import log_function_call
from models.document import Document


def input_group():
    return ui.div(
        ui.input_select(
            "document_type",
            "Type of document",
            choices=[
                "Training documents",
                "Validation-Plan",
                "URS",
                "FS",
                "Risk-Analysis",
                "Traceability Matrix",
                "Installation Qualification",
                "OQ-Testscripte",
                "PQ-Testscripte",
                "Validation-Report",
            ],
            selected="Training documents",
        ),
        ui.input_file(
            "uploaded_files", "Upload files", multiple=True, accept=[".pdf", ".xlsx"]
        ),
        ui.input_action_button(
            "btn_build_index", "Build index...", width="100%", disabled=True
        ),
    )


def output_group():
    return ui.div(
        ui.output_text_verbatim("txt_status"),
        ui.output_table("summary"),
        ui.output_ui("file_display"),
        ui.output_ui("import_to_ai"),
    )


def convert_image_to_base64(image, thumbnail=False, thumbnail_size=300):
    if thumbnail:
        image.thumbnail((thumbnail_size, thumbnail_size))
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    buffered.seek(0)

    # Encode byte stream to base64
    encoded_string = base64.b64encode(buffered.read()).decode("utf-8")
    return f"data:image/png;base64,{encoded_string}"


def image_accordion(name, images):
    return ui.accordion(
        ui.accordion_panel(
            f"{name} - {len(images)} pages",
            [
                ui.img(
                    {
                        "src": convert_image_to_base64(
                            img, thumbnail=True, thumbnail_size=800
                        )
                    }
                )
                for img in images
            ],
        ),
        open=False,
    )


@module.ui
def import_documents_ui():
    return ui.layout_sidebar(ui.sidebar(input_group(), width=350), output_group())


@module.server
def import_documents_server(input, output, session, processed_pdfs, rag_client):
    status_text = reactive.value("")

    @reactive.effect
    def update_ui():
        status_text.set(f"{len(processed_pdfs.get())} pdfs loaded...")
        ui.update_action_button(
            "btn_build_index", disabled=(len(processed_pdfs.get()) == 0)
        )

    @reactive.calc
    @log_function_call()
    def parsed_file():
        file: list[FileInfo] | None = input.uploaded_files()
        if file is None:
            return None

        result = {}
        document_list = []
        with ui.Progress(min=0, max=len(file)) as p:
            p.set(message="Extracting images", detail="This may take a while...")
            i = 0
            for f in file:
                i += 1
                p.set(i, message="Extracting images", detail=f["name"])
                logger.info(f"get images from file: {f}")
                images = convert_from_path(f["datapath"])
                result[f["name"]] = images
                doc = Document(f["name"], f["datapath"], images)
                document_list.append(doc)

        processed_pdfs.set(document_list)
        return result

    @reactive.effect
    @reactive.event(input.btn_build_index, ignore_none=True)
    def process_pdfs():
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
        status_text.set("Index created!")
        rag_client.set(RAG)

    @render.ui
    def file_display():
        images = parsed_file()

        if images is None:
            return ui.div("No file uploaded")

        accordions = []

        for name, img in images.items():
            accordions.append(image_accordion(name, img))

        return ui.div(
            accordions,
            ui.HTML("<br>"),
        )

    @render.text
    def txt_status():
        return status_text()
