from __future__ import annotations

import io
import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable

import streamlit as st

try:
    import m2c2_datakit as m2c2
except ImportError:
    m2c2 = None


st.set_page_config(page_title="LASSIE Data Pipeline", page_icon="🐕", layout="wide")

PLATFORMS = [
    "MetricWire",
    "Qualtrics",
    "MongoDB",
    "Multiple CSVs",
    "M2C2 Static",
    "M2C2 Production API (experimental)",
]


def require_package() -> None:
    if m2c2 is None:
        st.error(
            "The `m2datakit` package is not installed. Install the dependencies in "
            "`requirements.txt`, then restart the app."
        )
        st.stop()


def package_version() -> str:
    if m2c2 is None:
        return "not installed"
    try:
        value = m2c2.core.get_package_version()
        return str(value) if value is not None else "installed"
    except Exception:
        return getattr(m2c2, "__version__", "installed")


def build_summary_func_map() -> dict[str, Callable[..., Any]]:
    require_package()
    task_specs = {
        "Symbol Search": ("symbol_search", "summarize"),
        "Grid Memory": ("grid_memory", "summarize"),
        "Color Dots": ("color_dots", "summarize"),
        "Shopping List": ("shopping_list", "summarize"),
        "Trailmaking": ("trailmaking", "summarize"),
        "Go No Go": ("go_no_go", "summarize"),
        "Color Shapes": ("color_shapes", "summarize"),
        "Color Squares": ("color_squares", "summarize"),
        "Go No Go Fade": ("go_no_go_fade", "summarize"),
        "Color Match": ("color_match", "summarize"),
        "Stroop": ("stroop", "summarize"),
        "Digit Span": ("digit_span", "summarize"),
        "Odd or Even": ("even_odd", "summarize"),
        "JOLO": ("jolo", "summarize"),
        "Implicit Association Test": ("iat", "summarize"),
        "Face Naming Task": ("facename", "summarize"),
        "Symbol-Number Matching Task": ("symbol_number_matching", "summarize"),
        "Digit Symbol": ("symbol_number_matching", "summarize"),
    }
    available: dict[str, Callable[..., Any]] = {}
    for label, (module_name, function_name) in task_specs.items():
        module = getattr(m2c2.tasks, module_name, None)
        function = getattr(module, function_name, None) if module else None
        if callable(function):
            available[label] = function
    return available


def save_upload(uploaded_file: Any, directory: Path, filename: str | None = None) -> Path:
    target = directory / (filename or uploaded_file.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(uploaded_file.getbuffer())
    return target


def safe_extract_zip(uploaded_file: Any, destination: Path) -> None:
    with zipfile.ZipFile(io.BytesIO(uploaded_file.getvalue())) as archive:
        destination_resolved = destination.resolve()
        for member in archive.infolist():
            member_path = (destination / member.filename).resolve()
            if destination_resolved not in member_path.parents and member_path != destination_resolved:
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        archive.extractall(destination)


def zip_directory(directory: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(directory))
    return buffer.getvalue()


def render_outputs(output_dir: Path, platform_slug: str) -> None:
    files = [p for p in sorted(output_dir.rglob("*")) if p.is_file()]
    if not files:
        st.warning("The pipeline completed, but no export files were found.")
        return

    st.success(f"Pipeline complete. Created {len(files)} file(s).")
    st.download_button(
        "Download all outputs (.zip)",
        data=zip_directory(output_dir),
        file_name=f"lassie_{platform_slug}_outputs.zip",
        mime="application/zip",
        type="primary",
    )

    with st.expander("View individual output files", expanded=False):
        for path in files:
            st.download_button(
                f"Download {path.name}",
                data=path.read_bytes(),
                file_name=path.name,
                mime="application/octet-stream",
                key=f"download-{platform_slug}-{path}",
            )


def show_pipeline_preview(pipeline: Any) -> None:
    with st.expander("Pipeline details", expanded=False):
        try:
            contents = pipeline.whats_inside()
            if contents is not None:
                st.write(contents)
        except Exception as exc:
            st.caption(f"Preview unavailable: {exc}")

        for attribute in ("flat_scored", "summarized", "summary", "data"):
            value = getattr(pipeline, attribute, None)
            if value is not None:
                try:
                    st.write(f"**{attribute}**")
                    st.dataframe(value.head(100), use_container_width=True)
                    break
                except Exception:
                    continue


def run_pipeline(
    pipeline: Any,
    *,
    required_columns: list[str] | None,
    groupby_cols: list[str] | None,
    basename: str,
    output_dir: Path,
    create_codebook: bool = True,
) -> None:
    summary_func_map = build_summary_func_map()

    with st.status("Running LASSIE pipeline…", expanded=True) as status:
        if required_columns:
            st.write("Assuring required columns…")
            pipeline.assure(required_columns=required_columns)

        st.write("Scoring task data…")
        pipeline.score()

        st.write("Summarizing results…")
        summarize_kwargs: dict[str, Any] = {"summary_func_map": summary_func_map}
        if groupby_cols:
            summarize_kwargs["groupby_cols"] = groupby_cols
        pipeline.summarize(**summarize_kwargs)

        st.write("Exporting tidy outputs…")
        pipeline.export(file_basename=basename, directory=output_dir)

        if create_codebook and hasattr(pipeline, "export_codebook"):
            st.write("Generating codebook…")
            pipeline.export_codebook(filename=f"codebook_{basename}.md", directory=output_dir)

        status.update(label="LASSIE pipeline complete", state="complete", expanded=False)

    show_pipeline_preview(pipeline)


def metricwire_ui() -> None:
    st.subheader("MetricWire")
    st.write("Upload the **unzipped export as a ZIP file**. The app extracts it and finds JSON files recursively.")
    uploaded = st.file_uploader("MetricWire export (.zip)", type=["zip"], key="metricwire_zip")
    required_default = []
    if m2c2 is not None:
        required_default = list(
            getattr(m2c2.core.config.settings, "STANDARD_GROUPING_FOR_AGGREGATION_METRICWIRE", [])
        )
    required = st.text_input("Required columns", value=", ".join(required_default))
    groupby = st.text_input("Summary grouping columns", value=", ".join(required_default))

    if st.button("Run MetricWire pipeline", type="primary", disabled=uploaded is None):
        require_package()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            extracted = root / "metricwire"
            output = root / "outputs"
            extracted.mkdir()
            output.mkdir()
            safe_extract_zip(uploaded, extracted)
            json_files = list(extracted.rglob("*.json"))
            if not json_files:
                st.error("No JSON files were found in the uploaded ZIP archive.")
                return
            source_path = str(extracted / "**" / "*.json")
            pipeline = m2c2.core.pipeline.LASSIE().load(
                source_name="metricwire", source_path=source_path
            )
            run_pipeline(
                pipeline,
                required_columns=parse_columns(required),
                groupby_cols=parse_columns(groupby),
                basename="export_metricwire",
                output_dir=output,
            )
            render_outputs(output, "metricwire")


def qualtrics_ui() -> None:
    st.subheader("Qualtrics")
    uploaded = st.file_uploader("Qualtrics export (.csv)", type=["csv"], key="qualtrics_csv")
    required = st.text_input("Required columns", value="ResponseId", key="qualtrics_required")
    groupby = st.text_input("Summary grouping columns", value="ResponseId", key="qualtrics_groupby")

    if st.button("Run Qualtrics pipeline", type="primary", disabled=uploaded is None):
        require_package()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "outputs"
            output.mkdir()
            source = save_upload(uploaded, root)
            pipeline = m2c2.core.pipeline.LASSIE().load(
                source_name="qualtrics", source_path=str(source)
            )
            run_pipeline(
                pipeline,
                required_columns=parse_columns(required),
                groupby_cols=parse_columns(groupby),
                basename="export_qualtrics",
                output_dir=output,
            )
            render_outputs(output, "qualtrics")


def mongodb_ui() -> None:
    st.subheader("MongoDB")
    uploaded = st.file_uploader("MongoDB export (.json)", type=["json"], key="mongodb_json")
    required = st.text_input(
        "Required columns", value="study_uid, user_uid, activity_name", key="mongodb_required"
    )
    groupby = st.text_input("Summary grouping columns", value="user_uid", key="mongodb_groupby")

    if st.button("Run MongoDB pipeline", type="primary", disabled=uploaded is None):
        require_package()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "outputs"
            output.mkdir()
            source = save_upload(uploaded, root)
            pipeline = m2c2.core.pipeline.LASSIE().load(
                source_name="mongodb", source_path=str(source)
            )
            run_pipeline(
                pipeline,
                required_columns=parse_columns(required),
                groupby_cols=parse_columns(groupby),
                basename="export_mongodb",
                output_dir=output,
            )
            render_outputs(output, "mongodb")


def multicsv_ui() -> None:
    st.subheader("Multiple CSVs")
    st.write("Upload one trial-level CSV per activity, then map each file to its activity name.")
    uploads = st.file_uploader(
        "Task CSV files", type=["csv"], accept_multiple_files=True, key="multicsv_files"
    )
    mappings: dict[str, str] = {}
    for index, uploaded in enumerate(uploads or []):
        default_activity = Path(uploaded.name).stem.replace("_", " ").title()
        mappings[uploaded.name] = st.text_input(
            f"Activity name for {uploaded.name}", value=default_activity, key=f"activity-{index}"
        )
    required = st.text_input("Required columns", value="participant_id", key="multicsv_required")
    groupby = st.text_input(
        "Summary grouping columns (optional)", value="", key="multicsv_groupby"
    )

    if st.button("Run Multiple CSV pipeline", type="primary", disabled=not uploads):
        require_package()
        if len(set(mappings.values())) != len(mappings):
            st.error("Each uploaded CSV must have a unique activity name.")
            return
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "outputs"
            output.mkdir()
            source_map: dict[str, str] = {}
            for uploaded in uploads:
                source = save_upload(uploaded, root)
                source_map[mappings[uploaded.name]] = str(source)
            pipeline = m2c2.core.pipeline.LASSIE().load(
                source_name="multicsv", source_map=source_map
            )
            run_pipeline(
                pipeline,
                required_columns=parse_columns(required),
                groupby_cols=parse_columns(groupby),
                basename="export_multicsv",
                output_dir=output,
            )
            render_outputs(output, "multicsv")


def static_ui() -> None:
    st.subheader("M2C2 Static")
    uploaded = st.file_uploader("M2C2 results (.csv)", type=["csv"], key="static_csv")
    st.caption("The importer-recommended grouping columns are used when available.")

    if st.button("Run M2C2 Static pipeline", type="primary", disabled=uploaded is None):
        require_package()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "outputs"
            output.mkdir()
            source = save_upload(uploaded, root)
            pipeline = m2c2.core.pipeline.LASSIE().load(
                source_name="m2c2-static", source_path=str(source)
            )
            recommended = list(getattr(pipeline, "recommended_groupby_cols", []) or [])
            run_pipeline(
                pipeline,
                required_columns=recommended,
                groupby_cols=recommended,
                basename="export_m2c2_static",
                output_dir=output,
            )
            render_outputs(output, "m2c2_static")


def api_ui() -> None:
    st.subheader("M2C2 Production API")
    st.warning("Experimental feature: availability depends on the installed m2datakit version and API configuration.")
    api_url = st.text_input("API URL", value="https://api.m2c2kit.com")
    study_id = st.text_input("Study ID")
    username = st.text_input("Username", value=os.getenv("m2c2api_username", ""))
    password = st.text_input(
        "Password", value=os.getenv("m2c2api_password", ""), type="password"
    )
    limit = st.number_input("Record limit", min_value=1, max_value=100000, value=10)
    pipeline_name = st.text_input("Pipeline name", value="all_uploaded_data")

    disabled = not all([api_url, study_id, username, password])
    if st.button("Run API pipeline", type="primary", disabled=disabled):
        require_package()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "outputs"
            output.mkdir()
            pipeline = m2c2.core.pipeline.LASSIE().load(
                source_name="m2c2kit-api",
                source_path=api_url,
                study_id=study_id,
                username=username,
                password=password,
                payload={"limit": int(limit)},
                pipeline_name=pipeline_name,
            )
            run_pipeline(
                pipeline,
                required_columns=None,
                groupby_cols=None,
                basename="export_m2c2_api",
                output_dir=output,
            )
            render_outputs(output, "m2c2_api")


def parse_columns(value: str) -> list[str]:
    return [column.strip() for column in value.split(",") if column.strip()]


st.title("🐕 LASSIE: Universal M2C2 Data Pipeline")
st.caption("Load → Assure → Score → Summarize → Inspect → Export")

with st.sidebar:
    st.header("1. Select platform")
    platform = st.selectbox("Data platform", PLATFORMS, index=None, placeholder="Choose a platform…")
    st.divider()
    st.caption(f"m2datakit: {package_version()}")

if platform is None:
    st.info("Choose the source platform in the sidebar to begin.")
    st.markdown(
        """
        This app wraps the notebook workflow in a guided interface. Each platform gets its own
        uploader or connection form, while scoring, summarization, codebook generation, and export
        use the same LASSIE pipeline.
        """
    )
elif platform == "MetricWire":
    metricwire_ui()
elif platform == "Qualtrics":
    qualtrics_ui()
elif platform == "MongoDB":
    mongodb_ui()
elif platform == "Multiple CSVs":
    multicsv_ui()
elif platform == "M2C2 Static":
    static_ui()
elif platform == "M2C2 Production API (experimental)":
    api_ui()
