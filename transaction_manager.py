'''
* Transaction Manager never fails
* TM tracks the up/down status of all sites.
* If the TM requests a read on a replicated data item x for read-write transaction T and cannot get it due to failure,
the TM should try another site (all in the same step). If no relevant site is available, then T must wait.
* As mentioned above, if every site failed after a commit to x but before T began, then the read-only transaction should abort.

'''