Blockchain University Assignment at The University of Sydney

The specs for the assignment are located in the Assignment 2(v1).pdf file.

General synopsis:
This project is a peer-to-peer (P2P) blockchain system developed for the COMP3221 Distributed Systems course at The University of Sydney. The application operates as a distributed node that communicates with other peers over long-lived TCP connections to maintain a consistent, shared ledger. Key functionalities include validating JSON-formatted transactions using Ed25519 digital signatures, managing a local transaction pool, and executing a synchronous crash fault-tolerant consensus protocol to agree upon and append new blocks. The system is engineered with concurrent multithreading to simultaneously manage incoming server connections and coordinate continuous consensus rounds across the network.


Coding env: macOS

Versions: Python 3.11.2

Running Code Instruction:
- python3 -u main.py arguments


My code is run using python3 and the run.sh file which used a -u flag for flushing output.

