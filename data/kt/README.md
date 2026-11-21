# Knowledge tracing data

The ASSISTments 2009-2010 skill-builder data is not redistributed here.
Download it from the official ASSISTments data page (https://sites.google.com/site/assistmentsdata/),
prepare the train/test split as `assist2009_updated_train.csv` and `assist2009_updated_test.csv`
(one student per 3 lines: sequence length, skill ids, correctness), put them in this folder and run
`python -m scripts.train_kt`.

`dkt_assist.pt` (trained on that data) and `dkt_app.pt` are the trained models used by the app.
