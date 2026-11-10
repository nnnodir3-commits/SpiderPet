"""Local-only cooperative registry for multiple SpiderPet EXE processes.
Each instance periodically writes a small JSON heartbeat under the user's temp
folder. No network or remote desktop access is used.
"""
import json,os,tempfile,time,uuid,atexit
from pathlib import Path

class PeerRegistry:
    def __init__(self):
        self.directory=Path(os.environ.get('LOCALAPPDATA') or tempfile.gettempdir())/'SpiderPet_Peers_v26'
        self.directory.mkdir(parents=True,exist_ok=True)
        self.id=uuid.uuid4().hex
        self.filename=self.directory/f'peer_{os.getpid()}_{self.id}.json'
        self.last_write=0.
        self.last_read=0.
        self.peers=[]
        atexit.register(self.close)

    def close(self):
        try:self.filename.unlink(missing_ok=True)
        except OSError:pass

    def publish(self,x,y,size,mode='rest',fight_with='',fight_start=0.,force=False):
        now=time.time()
        if not force and now-self.last_write<0.12:return
        self.last_write=now
        data={'id':self.id,'pid':os.getpid(),'x':float(x),'y':float(y),'size':float(size),
              'mode':str(mode),'fight_with':str(fight_with),'fight_start':float(fight_start),
              'timestamp':now}
        # Atomic write prevents other instances observing partially-written JSON.
        tmp=self.directory/f'{self.id}.tmp'
        try:
            tmp.write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
            os.replace(tmp,self.filename)
        except OSError:pass

    def scan(self,force=False):
        now=time.time()
        if not force and now-self.last_read<0.20:return self.peers
        self.last_read=now
        peers=[]
        try:entries=list(self.directory.glob('peer_*.json'))
        except OSError:entries=[]
        for path in entries:
            if path==self.filename:continue
            try:
                if now-path.stat().st_mtime>12.:
                    # A crashed instance may leave its last heartbeat file.
                    try:path.unlink()
                    except OSError:pass
                    continue
                data=json.loads(path.read_text(encoding='utf-8'))
                if data.get('id')==self.id:continue
                timestamp=float(data.get('timestamp',0.))
                if now-timestamp>2.3 or timestamp-now>2.:continue
                data['x']=float(data['x']);data['y']=float(data['y']);data['size']=float(data['size'])
                if not all(abs(data[k])<100000 for k in ('x','y','size')):continue
                peers.append(data)
            except (OSError,ValueError,TypeError,KeyError):continue
        self.peers=peers
        return peers


def fight_phase(elapsed,role):
    """(label, attacker, step_fraction) for the two-way duel timeline."""
    if elapsed<0:return 'approach',False,0.
    if elapsed<0.85:return 'display',False,0.
    phase=elapsed-0.85
    if phase>=8.0:return 'finish',False,0.
    round_no=int(phase//1.0)
    fraction=phase%1.0
    attacker=(round_no%2)==role
    if fraction<0.42:
        return 'lunge' if attacker else 'brace',attacker,fraction/.42
    if fraction<0.74:
        return 'backoff' if attacker else 'hold',attacker,(fraction-.42)/.32
    return 'reset',attacker,(fraction-.74)/.26
