/* Compatibility stub for older launcher HTML. Never launch Home Helper on page load:
 * SAM may close the foreground Home even when the native process immediately exits.
 * Boot activity and an explicit Home Helper launch own startup and recovery. */
