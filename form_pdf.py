import pymupdf
from PIL import Image
import io
import os
import sys


MAX_SIZE_MB = 2
DPI = 300


def procesar_pdf(input_pdf, output_pdf):
    print("\n" + "=" * 60)
    print(f"Procesando: {os.path.basename(input_pdf)}")
    print("=" * 60)

    try:
        doc = pymupdf.open(input_pdf)

        print(f"Páginas: {len(doc)}")
        print(f"DPI: {DPI}")
        print("Conversión: escala de grises")
        print(f"Objetivo: < {MAX_SIZE_MB} MB\n")

        paginas = []

        zoom = DPI / 72
        matriz = pymupdf.Matrix(zoom, zoom)

        # ---------------------------------------------------------
        # Renderizar páginas a 300 DPI
        # ---------------------------------------------------------

        for numero, pagina in enumerate(doc):

            print(
                f"  Página {numero + 1}/{len(doc)}...",
                end=" ",
                flush=True
            )

            pix = pagina.get_pixmap(
                matrix=matriz,
                colorspace=pymupdf.csGRAY,
                alpha=False
            )

            img = Image.frombytes(
                "L",
                [pix.width, pix.height],
                pix.samples
            )

            paginas.append(img)

            print("OK")

        doc.close()

        # ---------------------------------------------------------
        # Diferentes niveles de compresión
        # ---------------------------------------------------------

        calidades = [70, 60, 50, 40, 30, 25, 20, 15, 10]

        for calidad in calidades:

            print(
                f"  Compresión JPEG calidad {calidad}...",
                end=" ",
                flush=True
            )

            pdf = pymupdf.open()

            for img in paginas:

                buffer = io.BytesIO()

                img.save(
                    buffer,
                    format="JPEG",
                    quality=calidad,
                    optimize=True
                )

                jpeg_data = buffer.getvalue()

                ancho_px, alto_px = img.size

                ancho_pt = ancho_px * 72 / DPI
                alto_pt = alto_px * 72 / DPI

                page = pdf.new_page(
                    width=ancho_pt,
                    height=alto_pt
                )

                page.insert_image(
                    page.rect,
                    stream=jpeg_data
                )

            # Crear carpeta destino si no existe
            os.makedirs(
                os.path.dirname(output_pdf),
                exist_ok=True
            )

            pdf.save(
                output_pdf,
                garbage=4,
                deflate=True,
                clean=True
            )

            pdf.close()

            size_bytes = os.path.getsize(output_pdf)
            size_mb = size_bytes / (1024 * 1024)

            print(f"{size_mb:.2f} MB")

            # -----------------------------------------------------
            # Si ya estamos debajo de 2 MB
            # -----------------------------------------------------

            if size_mb < MAX_SIZE_MB:

                print(
                    f"  ✓ Generado: "
                    f"{os.path.basename(output_pdf)} "
                    f"({size_mb:.2f} MB)"
                )

                return True

        # ---------------------------------------------------------
        # No se pudo llegar a 2 MB
        # ---------------------------------------------------------

        print(
            f"  ⚠ No fue posible reducirlo a menos de "
            f"{MAX_SIZE_MB} MB manteniendo {DPI} DPI."
        )

        return False

    except Exception as e:

        print(f"  ✗ ERROR: {e}")

        return False


def procesar_archivo(input_pdf, output_dir):
    """
    Procesa un PDF individual.
    """

    nombre = os.path.splitext(
        os.path.basename(input_pdf)
    )[0]

    output_pdf = os.path.join(
        output_dir,
        f"{nombre}_formateado.pdf"
    )

    return procesar_pdf(
        input_pdf,
        output_pdf
    )


def procesar_carpeta(carpeta):
    """
    Procesa todos los PDF de una carpeta.
    """

    carpeta = os.path.abspath(
        os.path.expanduser(carpeta)
    )

    if not os.path.isdir(carpeta):
        print(f"ERROR: No existe la carpeta:")
        print(carpeta)
        return

    output_dir = os.path.join(
        carpeta,
        "Formateados"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    archivos = [
        os.path.join(carpeta, archivo)
        for archivo in os.listdir(carpeta)
        if archivo.lower().endswith(".pdf")
        and os.path.isfile(
            os.path.join(carpeta, archivo)
        )
    ]

    if not archivos:
        print(f"No se encontraron archivos PDF en:")
        print(carpeta)
        return

    print("\n" + "=" * 60)
    print("FORMATEADOR DE PDF")
    print("=" * 60)
    print(f"Carpeta origen : {carpeta}")
    print(f"Carpeta destino: {output_dir}")
    print(f"PDF encontrados: {len(archivos)}")
    print("=" * 60)

    exitosos = 0
    errores = 0

    for archivo in sorted(archivos):

        if procesar_archivo(
            archivo,
            output_dir
        ):
            exitosos += 1
        else:
            errores += 1

    print("\n" + "=" * 60)
    print("PROCESAMIENTO TERMINADO")
    print("=" * 60)
    print(f"Total     : {len(archivos)}")
    print(f"Correctos : {exitosos}")
    print(f"Errores   : {errores}")
    print(f"Destino   : {output_dir}")
    print("=" * 60)


def main():

    if len(sys.argv) < 2:

        print("\nUso:")

        print(
            "  python form_pdf.py archivo.pdf"
        )

        print(
            "  python form_pdf.py carpeta/"
        )

        print(
            "  python form_pdf.py archivo1.pdf archivo2.pdf"
        )

        return

    argumentos = sys.argv[1:]

    archivos = []
    carpetas = []

    # ---------------------------------------------------------
    # Separar archivos y carpetas
    # ---------------------------------------------------------

    for argumento in argumentos:

        ruta = os.path.abspath(
            os.path.expanduser(argumento)
        )

        if os.path.isfile(ruta):

            if ruta.lower().endswith(".pdf"):
                archivos.append(ruta)

        elif os.path.isdir(ruta):

            carpetas.append(ruta)

        else:

            print(
                f"⚠ No existe: {argumento}"
            )

    # ---------------------------------------------------------
    # Procesar carpetas
    # ---------------------------------------------------------

    for carpeta in carpetas:

        procesar_carpeta(carpeta)

    # ---------------------------------------------------------
    # Procesar archivos individuales
    # ---------------------------------------------------------

    if archivos:

        # Si se pasan archivos individuales,
        # los resultados se guardan junto al archivo original
        # dentro de una carpeta Formateados.

        print("\n" + "=" * 60)
        print("ARCHIVOS INDIVIDUALES")
        print("=" * 60)

        for archivo in archivos:

            carpeta_origen = os.path.dirname(
                archivo
            )

            output_dir = os.path.join(
                carpeta_origen,
                "Formateados"
            )

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            procesar_archivo(
                archivo,
                output_dir
            )


if __name__ == "__main__":
    main()
