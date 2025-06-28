import pandas as pd
import json
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description="Prepare UFO shape time series")
    parser.add_argument('--input', default='nuforc_reports.csv.xz', help='Input CSV')
    parser.add_argument('--output', default='ufo_shapes.json', help='Output JSON')
    args = parser.parse_args()

    df = pd.read_csv(args.input, usecols=['date_time','shape'], parse_dates=['date_time'])
    df['year'] = df['date_time'].dt.year
    df = df[df['year'] >= 1940]
    df['shape'] = df['shape'].fillna('Unknown').str.title()

    top_shapes = df['shape'].value_counts()
    keep = top_shapes[top_shapes >= 200].index.tolist()
    df['shape'] = df['shape'].where(df['shape'].isin(keep), 'Other')

    counts = df.groupby(['year','shape']).size().reset_index(name='count')
    counts['decade'] = (counts['year'] // 10) * 10

    records = counts.to_dict('records')
    with open(args.output, 'w') as f:
        json.dump(records, f, separators=(',', ':'))

    size_kb = os.path.getsize(args.output) / 1024
    print(f"Wrote {args.output}: {size_kb:.1f} kB")


if __name__ == '__main__':
    main()
