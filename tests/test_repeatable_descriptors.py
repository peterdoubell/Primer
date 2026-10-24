"""Multiple lesions retain independent observations and a reproducible identity."""
import copy
import pytest
from primer.descriptor_reporting import render_descriptors


def plain(identifier, text, **extra):
    return {'id':identifier,'text':text,'segments':[{'text':text}],'slots':[],**extra}


@pytest.fixture
def schema():
    return {'investigations':[{'id':'mri','sections':[
        {'id':'lesions','label':'Lesions','repeatable':True,'repeat_label':'Lesion','normal':plain('none','No lesion.'),
         'findings':[plain('present','A lesion is present.',exclusive_group='type',invalidates_normal=['capsule']),
                     plain('cyst','A cyst is present.',exclusive_group='type'),
                     {'id':'size','text':'Size __ mm.','segments':[{'text':'Size '},{'slot':'diameter'},{'text':' mm.'}],
                      'slots':[{'id':'diameter','label':'Diameter','kind':'number','minimum':0}], 'requires_any':['present','cyst']}]},
        {'id':'capsule','label':'Capsule','normal':plain('capsule-normal','The capsule is intact.'),'findings':[]}
    ]}]}


def test_repeat_records_do_not_deduplicate_or_mix_values(schema):
    state={'investigation_id':'mri','selections':{'lesions':{'instances':[
        {'findings':{'present':{},'size':{'diameter':5}}},
        {'findings':{'cyst':{},'size':{'diameter':9}}}]}}}
    before=copy.deepcopy(state)
    result=render_descriptors(schema,state)
    assert result['valid'] and state==before
    assert 'Lesion 1:\nA lesion is present.\nSize 5 mm.' in result['text']
    assert 'Lesion 2:\nA cyst is present.\nSize 9 mm.' in result['text']
    state['selections']['lesions']['instances'][1]=copy.deepcopy(state['selections']['lesions']['instances'][0])
    assert render_descriptors(schema,state)['text'].count('Size 5 mm.')==2


@pytest.mark.parametrize('value',[
    {'instances':'bad'}, {'instances':[{}]}, {'instances':[{'normal':True}]},
    {'instances':[{'instances':[]}]}, {'normal':True,'instances':[{'findings':{'cyst':{}}}]},
    {'instances':[{'findings':{'size':{'diameter':5}}}]},
    {'instances':[{'findings':{'present':{},'cyst':{}}}]},
    {'instances':[{'findings':{'cyst':{}}}]*51},
    {'instances':[],'findings':None}, {'instances':[],'unknown':True}
])
def test_malformed_or_incomplete_records_produce_no_copyable_text(schema,value):
    result=render_descriptors(schema,{'investigation_id':'mri','selections':{'lesions':value}})
    assert not result['valid'] and result['text']==''


def test_repeat_parent_dependencies_and_cross_normals_remain_strict(schema):
    state={'investigation_id':'mri','selections':{'lesions':{'instances':[{'findings':{'present':{}}}]},'capsule':{'normal':True}}}
    result=render_descriptors(schema,state)
    assert not result['valid'] and 'conflicting_anatomic_normal' in {i['code'] for i in result['issues']}
    state['selections']['lesions']['instances']=[{'findings':{'cyst':{}}}]
    assert render_descriptors(schema,state)['valid']


def test_non_repeatable_schema_and_direct_instance_keys_cannot_accept_records(schema):
    schema['investigations'][0]['sections'][0]['repeatable']=False
    assert not render_descriptors(schema,{'investigation_id':'mri','selections':{'lesions':{'instances':[]}}})['valid']
    assert not render_descriptors(schema,{'investigation_id':'mri','selections':{'lesions@1':{'findings':{'cyst':{}}}}})['valid']
