from src.collect_corpora.libs.IO import IO

links = IO.read_json('google_links.json')
log_path = 'google_log.json'
log = IO.initialize_log(log_path)
print("Finished %d" % len(IO.which(range(len(links)), [link in log.keys() for link in links])))

for i, link in enumerate(links):
    if link in log.keys():
        continue

    print(link)
    log[link] = {}
    while True:
        print('%d/%d' % (i, len(links)))
        key = input('Accept (A) or Reject (R): ')
        if key.upper() == 'A':
            log[link]['accepted'] = True
            break
        elif key.upper() == 'R':
            log[link]['accepted'] = False
            break

    IO.write_json(log, log_path)