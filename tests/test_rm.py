import pytest
from pypdf import PdfReader

from .conftest import RESOURCES_ROOT, chdir, run_cli


def test_rm_incorrect_number_of_args(capsys, tmp_path):
    with chdir(tmp_path):
        exit_code = run_cli(["rm", str(RESOURCES_ROOT / "box.pdf")])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Missing argument" in captured.err


def test_rm_subset_ok(capsys, tmp_path):
    with chdir(tmp_path):
        exit_code = run_cli(
            [
                "rm",
                str(RESOURCES_ROOT / "GeoBase_NHNC1_Data_Model_UML_EN.pdf"),
                "13:15",
                "--output",
                "./out.pdf",
            ]
        )
    captured = capsys.readouterr()
    assert exit_code == 0, captured
    assert not captured.err
    inp_reader = PdfReader(
        RESOURCES_ROOT / "GeoBase_NHNC1_Data_Model_UML_EN.pdf"
    )
    out_reader = PdfReader(tmp_path / "out.pdf")
    assert len(out_reader.pages) == len(inp_reader.pages) - 2


@pytest.mark.parametrize(
    "page_range",
    ["a", "-", "1-", "1-1-1", "1:1:1:1"],
)
def test_rm_subset_invalid_args(capsys, tmp_path, page_range):
    with chdir(tmp_path):
        exit_code = run_cli(
            [
                "rm",
                str(RESOURCES_ROOT / "jpeg.pdf"),
                page_range,
                "--output",
                "./out.pdf",
            ]
        )
    captured = capsys.readouterr()
    assert exit_code == 2, captured
    assert "Invalid file path or page range provided" in captured.err


@pytest.mark.skip(reason="This check is not implemented yet")
def test_rm_subset_warn_on_missing_pages(capsys, tmp_path):
    with chdir(tmp_path):
        exit_code = run_cli(
            [
                "rm",
                str(RESOURCES_ROOT / "jpeg.pdf"),
                "2",
                "--output",
                "./out.pdf",
            ]
        )
    captured = capsys.readouterr()
    assert exit_code == 0, captured
    assert "WARN" in captured.out


@pytest.mark.xfail()
def test_rm_subset_ensure_reduced_size(tmp_path, two_pages_pdf_filepath):
    exit_code = run_cli(
        [
            "rm",
            str(two_pages_pdf_filepath),
            "0",
            "--output",
            str(tmp_path / "page1.pdf"),
        ]
    )
    assert exit_code == 0
    # The extracted PDF should only contain ONE image:
    embedded_images = extract_embedded_images(tmp_path / "page1.pdf")
    assert len(embedded_images) == 1

    exit_code = run_cli(
        [
            "rm",
            str(two_pages_pdf_filepath),
            "1",
            "--output",
            str(tmp_path / "page2.pdf"),
        ]
    )
    assert exit_code == 0
    # The extracted PDF should only contain ONE image:
    embedded_images = extract_embedded_images(tmp_path / "page2.pdf")
    assert len(embedded_images) == 1


def extract_embedded_images(pdf_filepath):
    images = []
    reader = PdfReader(pdf_filepath)
    for page in reader.pages:
        images.extend(page.images)
    return images


def test_rm_combine_files(pdf_file_100, pdf_file_abc, tmp_path, capsys):
    with chdir(tmp_path):
        output_pdf_path = tmp_path / "out.pdf"

        # Run pdfly rm command
        exit_code = run_cli(
            [
                "rm",
                str(pdf_file_100),
                "1:10:2",
                str(pdf_file_abc),
                "::2",
                str(pdf_file_abc),
                "1::2",
                "--output",
                str(output_pdf_path),
            ]
        )
        captured = capsys.readouterr()

        # Check if the command was successful
        assert exit_code == 0, captured.out

        # Extract text from the original and modified PDFs
        extracted_pages = []
        reader = PdfReader(output_pdf_path)
        for page in reader.pages:
            extracted_pages.append(page.extract_text())

        # Compare the extracted text
        l1 = [str(el) for el in list(range(0, 10, 2)) + list(range(10, 100))]
        assert extracted_pages == l1 + [
            "b",
            "d",
            "f",
            "h",
            "j",
            "l",
            "n",
            "p",
            "r",
            "t",
            "v",
            "x",
            "z",
            "a",
            "c",
            "e",
            "g",
            "i",
            "k",
            "m",
            "o",
            "q",
            "s",
            "u",
            "w",
            "y",
        ]


@pytest.mark.parametrize(
    ("page_range", "expected"),
    [
        ("22", [str(el) for el in range(100) if el != 22]),
        ("0:3", [str(el) for el in range(3, 100)]),
        (":3", [str(el) for el in range(3, 100)]),
        (":", []),
        ("5:", ["0", "1", "2", "3", "4"]),
        ("::2", [str(el) for el in list(range(100))[1::2]]),
        (
            "1:10:2",
            [str(el) for el in list(range(0, 10, 2)) + list(range(10, 100))],
        ),
        ("::1", []),
        ("::-1", []),
    ],
)
def test_rm_commands(pdf_file_100, capsys, tmp_path, page_range, expected):
    with chdir(tmp_path):
        output_pdf_path = tmp_path / "out.pdf"

        # Run pdfly rm command
        exit_code = run_cli(
            [
                "rm",
                str(pdf_file_100),
                page_range,
                "--output",
                str(output_pdf_path),
            ]
        )

        # Check if the command was successful
        assert exit_code == 0

        # Extract text from the original and modified PDFs
        extracted_pages = []
        reader = PdfReader(output_pdf_path)
        for page in reader.pages:
            extracted_pages.append(page.extract_text())

        # Compare the extracted text
        assert extracted_pages == expected
