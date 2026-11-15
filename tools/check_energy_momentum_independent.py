"""Independent arithmetic and differential-equation checks for the mechanics lab.

The work oracle advances velocity and position over small physical time intervals,
splitting a step at zero velocity and solving the static-friction inequality. It
never calls the JavaScript trajectory, event-time or energy implementations.
No historical proof files are overwritten; optional output must be a new file.
"""
import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'web/energy-momentum-lab.js'

def close(a, b, label, tolerance=3e-10):
    if not math.isfinite(a) or not math.isfinite(b) or abs(a-b) > tolerance * max(1, abs(a), abs(b)):
        raise AssertionError(f'{label}: {a} != {b}')

def step_oracle(s, end, steps=4000):
    """Independently integrate m dv/dt with Coulomb friction and exact substeps."""
    force = s['force'] - s['mass']*s['gravity']*math.sin(math.radians(s['angle']))
    bound = s['friction']*s['mass']*s['gravity']*math.cos(math.radians(s['angle']))
    q, velocity, distance = 0.0, s['initialVelocity'], 0.0
    if end == 0:
        return q, velocity, distance
    dt = end / steps
    for _ in range(steps):
        remaining = dt
        for _ in range(2):
            if velocity == 0 and abs(force) <= bound:
                break
            direction = math.copysign(1, velocity if velocity else force)
            acceleration = (force - bound*direction)/s['mass']
            step = remaining
            crossing = acceleration*velocity < 0 and abs(velocity/acceleration) <= remaining
            if crossing:
                step = abs(velocity/acceleration)
            next_velocity = 0.0 if crossing else velocity + acceleration*step
            dq = .5*(velocity+next_velocity)*step
            q += dq
            distance += abs(dq)
            velocity = next_velocity
            remaining -= step
            if remaining <= 0:
                break
    return q, velocity, distance

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    rng = random.Random(20261025)
    cases=[]
    for mass_a, mass_b, u, v, e, frame in itertools.product([.1,2,20],[.1,1,20],[-6,0,6],[-6,0,6],[0,.6,1],[-6,0,6]):
        cases.append({'mode':'collision','massA':mass_a,'massB':mass_b,'velocityA':u,'velocityB':v,'restitution':e,'frame':frame,'collisionTime':rng.choice([0,.25,1,4])})
    for mass,u,v,t,z in itertools.product([.01,.06,20],[-12,0,12],[-12,0,12],[.005,.1,2],[0,.25,.5,.75,1]):
        cases.append({'mode':'impulse','impactMass':mass,'incoming':u,'outgoing':v,'duration':t,'fraction':z})
    for mass,angle,mu,v,force in itertools.product([.1,2,1500],[-90,0,90],[0,.2,1],[-20,0,20],[-2500,0,2500]):
        cases.append({'mode':'work','mass':mass,'angle':angle,'friction':mu,'initialVelocity':v,'force':force,'workTime':rng.choice([0,.1,2,10]),'gravity':rng.choice([0,9.81,20])})
    cases.extend([{'mode':'work','mass':250,'initialVelocity':1,'force':2500,'angle':90,'gravity':10,'friction':0,'workTime':8},{'mode':'work','mass':1500,'initialVelocity':20,'force':0,'angle':0,'gravity':9.81,'friction':0,'workTime':0}])
    for _ in range(60):
        cases.append({'mode':'work','mass':rng.uniform(.1,50),'angle':rng.uniform(-60,60),'friction':rng.random(),'initialVelocity':rng.uniform(-8,8),'force':rng.uniform(-100,100),'workTime':rng.uniform(.1,10),'gravity':rng.uniform(0,20)})
    for power,t,eta in itertools.product([0,60,2000],[0,300,600],[0,20,100]):
        cases.append({'mode':'power','watts':power,'seconds':t,'efficiency':eta})
    script="""const fs=require('node:fs'),l=require('./web/energy-momentum-lab.js');
const states=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(states.map(s=>{const m=l.build(s);return {...m,points:undefined,checks:m.points.filter((p,i)=>i%20===0||i===m.points.length-1)};})));"""
    rows=json.loads(subprocess.run(['node','-e',script],input=json.dumps(cases),cwd=ROOT,text=True,capture_output=True,check=True).stdout)
    counts={mode:0 for mode in ['collision','impulse','work','power']}
    geometry_checks=0
    for raw,m in zip(cases,rows):
        s=m['state']; mode=s['mode'];counts[mode]+=1
        if mode=='collision':
            ma,mb,u,v,e,frame=[F(str(s[k])) for k in ['massA','massB','velocityA','velocityB','restitution','frame']]
            # Solve the independent 2×2 conservation/restitution linear system.
            M=ma+mb
            if u>v:
                vb=(ma*(1+e)*u+(mb-e*ma)*v)/M
                va=(ma*u+mb*v-mb*vb)/ma
                contact=F(2)/(u-v)
                close(m['eventTime'],float(contact),'contact time')
            else:
                va,vb=u,v; contact=None
                assert m['eventTime'] is None and not m['willCollide']
            close(m['vA'],float(va),'collision velocity A')
            close(m['vB'],float(vb),'collision velocity B')
            initial_k=(ma*(u-frame)**2+mb*(v-frame)**2)/2
            final_k=(ma*(va-frame)**2+mb*(vb-frame)**2)/2
            close(m['lost'],float(initial_k-final_k),'frame-invariant energy transfer')
            close(m['before']['pA']+m['before']['pB'],m['after']['pA']+m['after']['pB'],'momentum invariant')
            for p in m['checks']+[m['current']]:
                t=F(str(p['t']));before=contact is None or t<contact
                xa=F('-1.3')+u*t-frame*t;xb=F('1.3')+v*t-frame*t
                if not before:
                    xa+=(va-u)*(t-contact);xb+=(vb-v)*(t-contact)
                close(p['xA'],float(xa),'cart A position');close(p['xB'],float(xb),'cart B position')
                assert p['xB']-p['xA']>=.6-1e-10,'Carts cannot interpenetrate.'
                close(p['kA']+p['kB']+p['internal'],float(initial_k),'total energy at every checked time')
                geometry_checks+=2
        elif mode=='impulse':
            mass,u,v,duration=[F(str(s[k])) for k in ['impactMass','incoming','outgoing','duration']]
            expected_j=mass*(v-u);close(m['J'],float(expected_j),'impulse from momentum')
            # Quadrature of a separate piecewise-linear force definition; do not
            # call runtime pulse/cumulative helpers or compare against its samples.
            peak=2*expected_j/duration
            force=lambda t:float(peak)*(1-abs(2*t/float(duration)-1))
            h=float(duration)/1000
            integrated=h*(.5*force(0)+sum(force(i*h) for i in range(1,1000))+.5*force(float(duration)))
            close(integrated,float(expected_j),'quadrature force area')
            z=s['fraction'];t=z*float(duration)
            if z<=.5:
                partial=.5*t*force(t)
            else:
                partial=float(expected_j)-.5*(float(duration)-t)*force(t)
            close(m['current']['impulse'],partial,'partial triangular area')
            close(m['current']['velocity'],float(u)+partial/float(mass),'impulse response velocity')
            close(m['deltaK'],float(mass*(v*v-u*u)/2),'work from kinetic energy')
        elif mode=='work':
            p=m['current'];q,v,distance=step_oracle(s,s['workTime'])
            close(p['q'],q,'numerically integrated displacement',2e-9);close(p['v'],v,'numerically integrated velocity',2e-9);close(p['length'],distance,'numerically integrated travel',2e-9)
            for p in m['checks']+[m['current']]:
                close(s['mass']*p['a'],s['force']-m['weight']+p['frictionForce'],'Newton law')
                close(p['netWork'],.5*s['mass']*(p['v']**2-s['initialVelocity']**2),'work energy identity')
                energy_scale=max(1,abs(p['K']),abs(p['U']),abs(p['Q']),abs(p['K0']),abs(p['appliedWork']))
                assert abs(p['K']+p['U']+p['Q']-p['K0']-p['appliedWork']) <= 64*math.ulp(energy_scale), 'Energy residual exceeds 64 ulps of the largest energy term'
                assert p['Q']>=0 and p['pFriction']<=1e-9
                if p['v']==0 and p['a']==0: assert abs(p['frictionForce'])<=m['limit']+1e-9
                close(p['height'],p['q']*math.sin(math.radians(s['angle'])),'slope height')
                geometry_checks+=1
        else:
            p,t,eta=[F(str(s[k])) for k in ['watts','seconds','efficiency']]
            close(m['current']['input'],float(p*t),'power time')
            close(m['current']['useful'],float(p*t*eta/100),'useful transfer')
            close(m['current']['other'],float(p*t*(1-eta/100)),'other transfer')
    proof={'allPassed':True,'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'cases':counts,'totalCases':len(rows),'trajectoryChecks':geometry_checks,'methods':['Exact rational 2×2 collision constraints and Galilean transforms','Independent triangular-pulse quadrature','Small-step Newton-law integration with static friction and zero-velocity event splitting','Rational constant-power ledger'],'limits':'Numerical proof for the declared idealized models; not an empirical validation, production check, every lesson or whole-physics completion.'}
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as out:json.dump(proof,out,indent=2);out.write('\n')
    print(json.dumps(proof,indent=2))

if __name__=='__main__':main()
