import pytest
import os
import json
import pyecore.ecore as Ecore
from pyecore.resources import *
from pyecore.resources.json import JsonResource, JsonOptions


@pytest.fixture(scope='module')
def lib():
    package = Ecore.EPackage('mypackage')
    package.nsURI = 'http://simplemetamodel/1.0'
    package.nsPrefix = 'simplemm'
    AbsA = Ecore.EClass('AbsA', abstract=True)
    A = Ecore.EClass('A', superclass=(AbsA,))
    SubA = Ecore.EClass('SubA', superclass=(A,))
    MyRoot = Ecore.EClass('MyRoot')
    MyRoot.a_container = Ecore.EReference('a_container', eType=AbsA, upper=-1,
                                          containment=True)
    MyRoot.eStructuralFeatures.append(MyRoot.a_container)
    MyRoot.eStructuralFeatures.append(Ecore.EAttribute('trans',
                                                       eType=Ecore.EString,
                                                       transient=True))
    package.eClassifiers.extend([MyRoot, A, SubA, AbsA])
    package.MyRoot = MyRoot
    package.SubA = SubA
    package.A = A
    # we register the metamodel first
    global_registry[package.nsURI] = package
    return package


def test_json_resource_save_metamodel(tmpdir, lib):
    f = tmpdir.mkdir('pyecore-tmp').join('test.json')
    resource = JsonResource(URI(str(f)))
    resource.append(lib)
    resource.save()

    # we read the model
    resource = JsonResource(URI(str(f)))
    resource.load()
    root = resource.contents[0]
    assert len(root.eContents) == len(lib.eContents)
    assert isinstance(root, lib.eClass.python_class)


def test_json_resource_save_metamodel_uri(tmpdir, lib):
    f = tmpdir.mkdir('pyecore-tmp').join('test.json')
    resource = JsonResource(URI(str(f)), use_uuid=True)
    resource.append(lib)
    resource.save()

    # we read the model
    resource = JsonResource(URI(str(f)))
    resource.load()
    root = resource.contents[0]
    assert len(root.eContents) == len(lib.eContents)
    assert isinstance(root, lib.eClass.python_class)


def test_json_resource_createset(tmpdir, lib):
    f = tmpdir.mkdir('pyecore-tmp').join('test.json')
    resource = JsonResource(URI(str(f)))

    # we create some instances
    root = lib.MyRoot()
    a1 = lib.A()
    suba1 = lib.SubA()
    root.a_container.extend([a1, suba1])
    root.trans = 'transient_value'

    # we add the elements to the resource
    resource.append(root)
    resource.save()

    # we read the model
    resource = JsonResource(URI(str(f)))
    resource.load()
    assert resource.contents != []
    assert len(resource.contents[0].eContents) == 2


def test_json_resource_createSaveModifyRead(tmpdir, lib):
    f = tmpdir.mkdir('pyecore-tmp').join('test.json')
    resource = JsonResource(URI(str(f)))

    # we create some instances
    root = lib.MyRoot()
    a1 = lib.A()
    suba1 = lib.SubA()
    root.a_container.extend([a1, suba1])

    # we add the elements to the resource
    resource.append(root)
    resource.save()

    # we add more instances
    a2 = lib.A()
    root.a_container.append(a2)

    # we save again
    resource.save()

    # we read the model
    resource = JsonResource(URI(str(f)))
    resource.load()
    assert resource.contents != []
    assert len(resource.contents[0].eContents) == 3


# Defines a small metamodel
eClass = Ecore.EPackage('pack', nsURI='http://test_pack/1.0', nsPrefix='pack')
nsURI = 'http://tst/1.0'

@Ecore.EMetaclass
class A(object):
    child = Ecore.EReference(containment=True, upper=-1)
    imply = Ecore.EReference()
    ref_by = Ecore.EReference()
    distant = Ecore.EReference(eType=Ecore.EObject)


A.child.eType = A
A.imply.eType = A
A.ref_by.eType = A


@Ecore.EMetaclass
class Point(object):
    x = Ecore.EAttribute(eType=Ecore.EDouble)
    y = Ecore.EAttribute(eType=Ecore.EDouble)
    z = Ecore.EAttribute(eType=Ecore.EDouble)


def test_json_resource_save_static_metamodel(tmpdir):
    f = tmpdir.mkdir('pyecore-tmp').join('test.json')
    resource = JsonResource(URI(str(f)))

    # we add the elements to the resource
    resource.append(eClass)
    resource.save()

    # we read the model
    resource = JsonResource(URI(str(f)))
    resource.load()
    assert resource.contents != []
    assert len(resource.contents[0].eContents) == 2

    root = resource.contents[0]
    assert root.eContents[0].name == 'A'


def test_json_option_serialize_default_values(tmpdir):
    f = tmpdir.mkdir('pyecore-tmp').join('test.json')
    resource = JsonResource(URI(str(f)))

    p = Point()
    p.x = 0.0
    p.z = 0.0
    resource.append(p)
    resource.save(options={JsonOptions.SERIALIZE_DEFAULT_VALUES: True})

    dct = json.load(open(str(f)))
    assert dct['x'] == 0.0
    assert dct['z'] == 0.0
    assert 'y' not in dct


def test_json_save_multiple_roots(tmpdir):
    A = Ecore.EClass('A')
    A.eStructuralFeatures.append(Ecore.EAttribute('name', Ecore.EString))
    pack = Ecore.EPackage('pack', 'packuri', 'pack')
    pack.eClassifiers.append(A)

    f = tmpdir.mkdir('pyecore-tmp').join('multiple.json')
    resource = JsonResource(URI(str(f)))
    resource.append(A(name='root1'))
    resource.append(A(name='root2'))
    resource.save()

    dct = json.load(open(str(f)))
    assert type(dct) is list
    assert dct[0]['name'] == 'root1'
    assert dct[1]['name'] == 'root2'


def test_json_save_multiple_roots_roundtrip(tmpdir):
    A = Ecore.EClass('A')
    A.eStructuralFeatures.append(Ecore.EAttribute('name', Ecore.EString))
    pack = Ecore.EPackage('pack', 'packuri', 'pack')
    pack.eClassifiers.append(A)

    f = tmpdir.mkdir('pyecore-tmp').join('multiple.json')
    resource = JsonResource(URI(str(f)))
    resource.append(A(name='root1'))
    resource.append(A(name='root2'))
    resource.save()

    global_registry[pack.nsURI] = pack
    resource = JsonResource(URI(str(f)))
    resource.load()
    assert len(resource.contents) == 2
    assert resource.contents[0].name == 'root1'
    assert resource.contents[1].name == 'root2'
    del global_registry[pack.nsURI]
