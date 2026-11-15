"""Paso 0: convierte el csv.gz crudo en un parquet por foto_mes. Reanudable.

Uso (repetir hasta que diga TODO COMPLETO):
    python src/00_convertir_a_parquet.py <csv.gz> <carpeta_salida> [segundos_max]

- Streaming con poca RAM (pensado para 3 GB).
- El crudo viene ordenado por foto_mes: cada mes se escribe a <yyyymm>.parquet.tmp
  y se renombra a <yyyymm>.parquet recién cuando el mes está completo.
- Al retomar, salta las filas de los meses ya terminados.
- Tipos: todo float64 salvo foto_mes (int64) y numero_de_cliente (int64).
  Un cliente viene como '4.8e+07' en el crudo: se lee float64 y se castea a int64.
"""
import glob
import os
import subprocess
import sys
import time

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pcsv
import pyarrow.parquet as pq

ENTEROS = {"foto_mes"}
MESES_ESPERADOS = 32  # 201901..202108


def main(csv_gz, salida, presupuesto=120):
    t0 = time.time()
    os.makedirs(salida, exist_ok=True)

    hechos = sorted(glob.glob(os.path.join(salida, "??????.parquet")))
    saltar = sum(pq.ParquetFile(p).metadata.num_rows for p in hechos)
    print(f"Meses completos: {len(hechos)} · filas a saltar: {saltar:,}", flush=True)
    if len(hechos) >= MESES_ESPERADOS:
        print("TODO COMPLETO", flush=True)
        return

    cmd = (f'(zcat "{csv_gz}" | head -n 1; '
           f'zcat "{csv_gz}" | tail -n +{saltar + 2})')
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, executable="/bin/bash")

    cab = pcsv.open_csv(proc.stdout, read_options=pcsv.ReadOptions(block_size=1 << 20))
    nombres = cab.schema.names
    # reabrir con tipos: el primer reader consumió 1 MB; se reinicia el proceso
    proc.kill()
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, executable="/bin/bash")
    tipos = {c: (pa.int64() if c in ENTEROS else pa.float64()) for c in nombres}
    reader = pcsv.open_csv(
        proc.stdout,
        read_options=pcsv.ReadOptions(block_size=32 << 20),
        convert_options=pcsv.ConvertOptions(column_types=tipos),
    )
    esquema = reader.schema.set(
        reader.schema.get_field_index("numero_de_cliente"),
        pa.field("numero_de_cliente", pa.int64()),
    )

    actual, writer, filas_mes, ultimo = None, None, 0, 0

    def cerrar(completo):
        nonlocal writer
        if writer is None:
            return
        writer.close()
        writer = None
        tmp = os.path.join(salida, f"{actual}.parquet.tmp")
        if completo:
            os.rename(tmp, os.path.join(salida, f"{actual}.parquet"))
            print(f"  {actual} OK · {filas_mes:,} filas · {time.time()-t0:.0f} s", flush=True)

    agotado = True
    for batch in reader:
        tabla = pa.Table.from_batches([batch])
        i = tabla.schema.get_field_index("numero_de_cliente")
        tabla = tabla.set_column(i, "numero_de_cliente", tabla["numero_de_cliente"].cast(pa.int64()))
        for mes in pc.unique(tabla["foto_mes"]).to_pylist():
            if mes < ultimo:
                raise SystemExit(f"El crudo no está ordenado por mes ({mes} después de {ultimo})")
            if mes != actual:
                cerrar(completo=True)  # el mes anterior terminó (datos ordenados)
                actual, filas_mes, ultimo = mes, 0, mes
                writer = pq.ParquetWriter(
                    os.path.join(salida, f"{mes}.parquet.tmp"), esquema, compression="zstd")
            parte = tabla.filter(pc.equal(tabla["foto_mes"], mes))
            writer.write_table(parte)
            filas_mes += parte.num_rows
        if time.time() - t0 > presupuesto:
            agotado = False
            break
    proc.kill()
    # si se leyó todo el archivo, el último mes también está completo
    cerrar(completo=agotado)
    total = len(glob.glob(os.path.join(salida, "??????.parquet")))
    print(("TODO COMPLETO" if total >= MESES_ESPERADOS else f"Parcial: {total}/{MESES_ESPERADOS} meses")
          + f" · {time.time()-t0:.0f} s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 120)
