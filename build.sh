#!/bin/bash

cd docs
make html
cd ..
python -m unittest tests/test_json_timeseries.py && python -m build && twine check dist/* && twine upload --repository-url https://test.pypi.org/legacy/ dist/*
