"""An empty status snapshot or a dead client is never completion evidence."""
class Completion:
 def __init__(self,app,package_path,client):
  self.app=app;self.package_path=package_path;self.client=client;self.complete=False
 def feed(self,event):
  if not isinstance(event,dict):return False
  d=event.get('details')
  if not isinstance(d,dict):return False
  ok=(event.get('id')==self.app and type(event.get('statusValue')) is int
      and event['statusValue']==30 and event.get('returnValue') is not False
      and 'errorCode' not in event and 'errorCode' not in d and d.get('packageId')==self.app
      and d.get('ipkFile')==self.package_path and d.get('client')==self.client)
  if ok:self.complete=True
  return ok
