from dejavu import Dejavu

config = {
    "database": {
        "host": "127.0.0.1",
        "user": "root",
        "passwd": "root",
        "db": "dejavu",
    }
}

djv = Dejavu(config)

djv.fingerprint_directory("mp3", [".mp3"], 3)

print djv.db.get_num_fingerprints()


