# Collection of corpora #

This part of the project is done locally on my computer.

#### How do I get set up?

##### Requirements

- You need to have `selenium` set up
- An mongo-db instance

The analysis steps are in separate folders:

- `scrape_references` which scrapes from IEEE, ISCA, PubMed and WoS, data is stored in `scrape_references/data`, the raw results are not saved here, because I don't have the copyrights
- `import_references` puts results from all databases into one format
  - `import_data.py` puts the data into one common format
  - `write_to_db.py` puts them into the mongoDB
- `insert_reviewed_databases` inserts results from different published literature reviews
- `query_database_engines` adds results from database engines like Kaggle and Google Dataset
- `find_and_annotate_corpora` goes through this list and manually checks all registered publications
- `fix_corpora` contains a script to annotate missing information in the GEMEP corpus



#### Why are my results not identical with your results?

I ran the analysis on the 1st of April 2020, since then new papers might have appeared, the search engines might have changed.


