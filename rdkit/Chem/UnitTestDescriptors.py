#
#  Copyright (C) 2007-2017 Greg Landrum
#
#   @@ All Rights Reserved @@
#  This file is part of the RDKit.
#  The contents are covered by the terms of the BSD license
#  which is included in the file license.txt, found at the root
#  of the RDKit source tree.
#
""" General descriptor testing code

"""
from __future__ import print_function
from rdkit import RDConfig
import unittest, os.path
import io
from rdkit.six.moves import cPickle
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import AllChem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem import Lipinski
import numpy as np


def feq(n1, n2, tol=1e-4):
  return abs(n1 - n2) <= tol


class TestCase(unittest.TestCase):

  def testGithub1287(self):
    smis = ('CCC', )
    for smi in smis:
      m = Chem.MolFromSmiles(smi)
      self.assertTrue(m)
      for nm, fn in Descriptors._descList:
        try:
          v = fn(m)
        except Exception:
          import traceback
          traceback.print_exc()
          raise AssertionError('SMILES: %s; Descriptor: %s' % (smi, nm))

  def testBadAtomHandling(self):
    smis = ('CC[Pu]', 'CC[*]')
    for smi in smis:
      m = Chem.MolFromSmiles(smi)
      self.assertTrue(m)
      for nm, fn in Descriptors._descList:
        try:
          v = fn(m)
        except Exception:
          import traceback
          traceback.print_exc()
          raise AssertionError('SMILES: %s; Descriptor: %s' % (smi, nm))

  def testMolFormula(self):
    for (smiles, expected) in (("[NH4+]", "H4N+"),
                               ("c1ccccc1", "C6H6"),
                               ("C1CCCCC1", "C6H12"),
                               ("c1ccccc1O", "C6H6O"),
                               ("C1CCCCC1O", "C6H12O"),
                               ("C1CCCCC1=O", "C6H10O"),
                               ("N[Na]", "H2NNa"),
                               ("[C-][C-]", "C2-2"),
                               ("[H]", "H"),
                               ("[H-1]", "H-"),
                               ("[H-1]", "H-"),
                               ("[CH2]", "CH2"),
                               ("[He-2]", "He-2"),
                               ("[U+3]", "U+3"), ):
      mol = Chem.MolFromSmiles(smiles)
      actual = AllChem.CalcMolFormula(mol)
      self.assertEqual(actual, expected)

  def testMQNDetails(self):
    refFile = os.path.join(RDConfig.RDCodeDir, 'Chem', 'test_data', 'MQNs_regress.pkl')
    refFile2 = os.path.join(RDConfig.RDCodeDir, 'Chem', 'test_data', 'MQNs_non_strict_regress.pkl')
    # figure out which definition we are currently using
    m = Chem.MolFromSmiles("CC(C)(C)c1cc(O)c(cc1O)C(C)(C)C")
    if Lipinski.NumRotatableBonds(m) == 2:
      refFile = refFile2

    with open(refFile, 'r') as intf:
      buf = intf.read().replace('\r\n', '\n').encode('utf-8')
      intf.close()
    with io.BytesIO(buf) as inf:
      pkl = inf.read()
    refData = cPickle.loads(pkl, encoding='bytes')
    fn = os.path.join(RDConfig.RDCodeDir, 'Chem', 'test_data', 'aromat_regress.txt')
    ms = [x for x in Chem.SmilesMolSupplier(fn, delimiter='\t')]
    refData2 = []
    for i, m in enumerate(ms):
      mqns = rdMolDescriptors.MQNs_(m)
      refData2.append((m, mqns))
      if mqns != refData[i][1]:
        indices = [(j, x, y) for j, x, y in zip(range(len(mqns)), mqns, refData[i][1]) if x != y]
        print(i, Chem.MolToSmiles(m), indices)
      self.assertEqual(mqns, refData[i][1])

  def testMQN(self):
    m = Chem.MolFromSmiles("CC(C)(C)c1cc(O)c(cc1O)C(C)(C)C")
    if Lipinski.NumRotatableBonds(m) == 2:
      tgt = np.array(
        [42917, 274, 870, 621, 135, 1582, 29, 3147, 5463, 6999, 470, 62588, 19055, 4424, 309, 24061,
         17820, 1, 9303, 24146, 16076, 5560, 4262, 646, 746, 13725, 5430, 2629, 362, 24211, 15939,
         292, 41, 20, 1852, 5642, 31, 9, 1, 2, 3060, 1750])
    else:
      tgt = np.array(
        [42917, 274, 870, 621, 135, 1582, 29, 3147, 5463, 6999, 470, 62588, 19055, 4424, 309, 24061,
         17820, 1, 8314, 24146, 16076, 5560, 4262, 646, 746, 13725, 5430, 2629, 362, 24211, 15939,
         292, 41, 20, 1852, 5642, 31, 9, 1, 2, 3060, 1750])
    fn = os.path.join(RDConfig.RDCodeDir, 'Chem', 'test_data', 'aromat_regress.txt')
    ms = [x for x in Chem.SmilesMolSupplier(fn, delimiter='\t')]
    vs = np.zeros((42, ), np.int32)
    for m in ms:
      vs += rdMolDescriptors.MQNs_(m)
    self.assertFalse(False in (vs == tgt))
    
  def testNumChiralCenters(self):
    for (smiles, expected) in (("C", 0),
                          ("c1ccccc1", 0),
                          ("CC(Cl)Br", 1),
                          ("CCC(C)C(Cl)Br", 2),
                          ("CCC(C(Cl)Br)C(F)I", 3),
                          ("[H][C@](F)(I)C(CC)C(Cl)Br", 3),
                          ("[H][C@](F)(I)[C@@]([H])(CC)C(Cl)Br", 3), ):
      mol = Chem.MolFromSmiles(smiles)
      actual = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
      self.assertEqual(actual, expected)
  
  
  def testNumSpecificChiralCenters(self):
    for (smiles, expected) in (("C", 0),
                          ("c1ccccc1", 0),
                          ("CC(Cl)Br", 0),
                          ("CCC(C)C(Cl)Br", 0),
                          ("CCC(C(Cl)Br)C(F)I", 0),
                          ("[H][C@](F)(I)C(CC)C(Cl)Br", 1),
                          ("[H][C@](F)(I)[C@@]([H])(CC)C(Cl)Br", 2), ):
      mol = Chem.MolFromSmiles(smiles)
      actual = len(Chem.FindMolChiralCenters(mol))
      self.assertEqual(actual, expected)
  
  def testNumUnspecificChiralCenters(self):
    for (smiles, expected) in (("C", 0),
                          ("c1ccccc1", 0),
                          ("CC(Cl)Br", 1),
                          ("CCC(C)C(Cl)Br", 2),
                          ("CCC(C(Cl)Br)C(F)I", 3),
                          ("[H][C@](F)(I)C(CC)C(Cl)Br", 2),
                          ("[H][C@](F)(I)[C@@]([H])(CC)C(Cl)Br", 1), ):
      mol = Chem.MolFromSmiles(smiles)
      actual = sum(1 for x in Chem.FindMolChiralCenters(mol, includeUnassigned=True) 
+              if x[1] == '?')
      self.assertEqual(actual, expected)                      
                          

# - - - - -
if __name__ == '__main__':
  unittest.main()
