import os
from io import BytesIO

import boto3
from fpdf import FPDF

bucket_name = os.environ.get("AWS_BUCKET_NAME")
s3 = boto3.resource('s3')
bucket = s3.Bucket(bucket_name)


def generate(file_name, text: list):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Times', 'B', 24)
    for line in text:
        pdf.cell(200, 10, line)
        pdf.ln()

    byte_string = pdf.output(dest='S')
    stream = BytesIO(byte_string)
    stream.seek(0)
    bucket.put_object(Key=file_name, Body=stream)
    return f"http://{bucket_name}.s3.amazonaws.com/{file_name}"
