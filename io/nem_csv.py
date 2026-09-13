# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.19.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

import polars as pl


# +
def split_tables_by_bytes(raw: bytes) -> dict[str, tuple[int, int]]:
    """
    Still not faster than rust. Maybe rust uses multiple threads.
    Also, this version uses more memory
    """
    # 73:  # b"I"
    # 67:  # b"C"
    # 44:  # b","
    tables = {}
    n = len(raw)

    # First table
    if n >= 2 and raw[0] == 73 and raw[1] == 44:
        start = 0
    else:
        i = raw.find(b'\nI,')
        if i == -1:
            return tables
        else:
            start = i + 1
    while True:
        # Find next table boundary.
        i = raw.find(b'\nI,', start + 1)

        if i == -1:
            end = raw.find(b'\nC,', start + 1)
            if end == -1:
                end = n
            next_start = -1
        else:
            end = i + 1
            next_start = i

        # Only I tables.
        if raw[start] == 73:  # b"I"
            # I,<table_id>,<table_name>,...
            comma1 = raw.find(b',', start + 2)
            comma2 = raw.find(b',', comma1 + 1)

            if comma1 != -1 and comma2 != -1:
                name = raw[comma1 + 1 : comma2].decode()
                tables[name] = (start, end)

        if next_start == -1:
            break

        start = next_start + 1
    return tables


def read_zip_csv(
    zipfile: ZipFile,
    filename: str,
    tables: list = None,
    columns: list[str] | dict[str, list[str]] = None,
    schemas: dict[str, list[str] | dict[str, pl.DataType]] = None,
    conditions: dict[str, pl.Expr | list[tuple]] = None,
    header_to_lowercase: bool = True,
    split_version: int = 1,
) -> dict:
    raw = zipfile.read(filename)
    t0 = time.time()  # xxx
    table_blocks = split_tables_by_bytes(raw)
    print(
        f'split_tables_by_bytes: {time.time() - t0:.3f}s. size: {len(raw) / (1024**2):.3f} MiB'
    )  # xxx

    dfs = {}
    for table_name, (s, e) in table_blocks.items():
        if tables is not None and table_name not in tables:
            continue
        cols = None if columns is None else columns.get(table_name)
        schema_overrides = None if schemas is None else schemas.get(table_name)
        for infer_schema_length in [100, 1000, 10000, None]:
            try:
                t1 = time.time()  # xxx
                df = pl.read_csv(
                    raw[s:e], # has memory copy
                    columns=cols,
                    schema_overrides=schema_overrides,
                    batch_size=8192 // 4,
                    has_header=True,
                    try_parse_dates=True,
                    # ignore_errors / truncate_ragged_lines shouldn't be needed now —
                    # try dropping them once this works, to confirm no rows are being silently eaten
                    ignore_errors=True,
                    truncate_ragged_lines=True,
                    infer_schema_length=infer_schema_length,
                )
                print(f'{table_name}: read_csv: {time.time() - t1:.3f}s')  # xxx
                break
            except pl.exceptions.ComputeError:
                continue
        if header_to_lowercase:
            df = df.rename(str.lower)
            table_name = table_name.lower()
        if conditions is not None:
            df = apply_filters(df, conditions.get(table_name, None))

        dfs[table_name] = df

    return dfs


# -

# ## test scan_csvpanicwarning

# +
import io
import polars as pl

raw = b"D,x\nI,s,t,v\nD,s,t,2\nE,finished\n"

lf = pl.scan_csv(
    io.BytesIO(raw),
    skip_lines=1,
    has_header=True,
    n_rows=1,
    ignore_errors=True,
    truncate_ragged_lines=True,
)
df = lf.collect()
print(df)
