# btrfsbalance
Calculate if btrfs balance is needed and balance one block at a time, until balance is not needed anymore

Criteria when to rebalance:

https://support.cumulusnetworks.com/hc/en-us/articles/360037394933-When-to-Rebalance-BTRFS-Partitions

What chunks to balance is based on this idea:

https://github.com/knorrie/python-btrfs/blob/master/bin/btrfs-balance-least-used
