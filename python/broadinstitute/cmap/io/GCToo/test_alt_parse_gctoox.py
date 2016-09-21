import logging
import setup_GCToo_logger as setup_logger
import unittest
import os
import pandas as pd
import numpy as np
import GCToo
import h5py
import alt_parse_gctoox
from pandas.util.testing import assert_frame_equal

__author__ = "Oana Enache"
__email__ = "oana@broadinstitute.org"

FUNCTIONAL_TESTS_PATH = "functional_tests"

logger = logging.getLogger(setup_logger.LOGGER_NAME)

version_node = "version"
rid_node = "/0/META/ROW/id"
cid_node = "/0/META/COL/id"
data_node = "/0/DATA/0/matrix"
row_meta_group_node = "/0/META/ROW"
col_meta_group_node = "/0/META/COL"

# Some notes on testing conventions (more in cuppers convention doc):
#	(1) Use "self.assert..." over "assert"
#		- self.assert* methods: https://docs.python.org/2.7/library/unittest.html#assert-methods
# 	(2) For testing exceptions use:
#		with self.assertRaises(some_exception) as context:
#			[call method that should raise some_exception]
#		self.assertEqual(str(context.exception), "expected exception message")


class TestAltParseGCToox(unittest.TestCase):
	def test_get_all_id_values(self):
		# expected content
		expected_cid_keys = ['LJP005_A375_24H:DMSO:-666', 'LJP005_A375_24H:BRD-K76908866:10']
		expected_rid_keys = ['200814_at', '218597_s_at', '217140_s_at']
		expected_values = np.array(range(0,3))
		
		# set up and call method
		id_dict = {}
		mini_hdf5 = h5py.File(FUNCTIONAL_TESTS_PATH + "/mini_gctx_with_metadata_n2x3.gctx", "r", driver = "core")
		rid_dset = mini_hdf5[rid_node]
		cid_dset = mini_hdf5[cid_node]
		alt_parse_gctoox.get_all_id_values(rid_dset, cid_dset, id_dict)

		self.assertTrue(id_dict['rids']['full_id_list'].values.all() == expected_values.all(),
			"All rid indexes differ from expected {}: {}".format(expected_values, id_dict['rids']['full_id_list'].values))
		self.assertTrue(id_dict['cids']['full_id_list'].values.all() == expected_values.all(),
			"All cid indexes differ from expected {}: {}".format(expected_values, id_dict['cids']['full_id_list'].values))
		self.assertTrue(list(id_dict['rids']['full_id_list'].keys()) == expected_rid_keys, 
			"All rid values differ from expected {}: {}".format(expected_rid_keys, list(id_dict['rids']['full_id_list'].keys())))
		self.assertTrue(list(id_dict['cids']['full_id_list'].keys()) == expected_cid_keys, 
			"All cid values differ from expected {}: {}".format(expected_cid_keys, list(id_dict['cids']['full_id_list'].keys())))


	def test_get_ordered_slice_indexes(self):
		# expected relevant dict output
		expected_indexes = [0,1,3]
		expected_values = ['id1', 'id2', 'id4']
		# populate sample id dict
		full_df = pd.DataFrame(range(0,6), index = ["id1", "id2", "id3", "id4", "id5", "id6"]).transpose()
		test_dict = {}
		test_dict["rids"] = {}
		test_dict["rids"]["full_id_list"] = full_df
		alt_parse_gctoox.get_ordered_slice_indexes("rids", test_dict, ['id4', 'id1', 'id2'])
		self.assertTrue(test_dict["rids"]["slice_indexes"] == expected_indexes,
			"Ordered expected indexes {} not found: {} instead".format(expected_indexes, test_dict["rids"]["slice_indexes"]))
		self.assertTrue(test_dict["rids"]["slice_values"] == expected_values,
			"Ordered expected values {} not found: {} instead".format(expected_values, test_dict["rids"]["slice_values"]))


	def test_make_id_info_dict(self):
		mini_hdf5 = h5py.File(FUNCTIONAL_TESTS_PATH + "/mini_gctx_with_metadata_n2x3.gctx", "r", driver = "core")
		rid_dset = mini_hdf5[rid_node]
		cid_dset = mini_hdf5[cid_node]

		# basic check the expected keys are there: No slicing
		case1 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, None, None)
		self.assertTrue(case1.keys() == ['slice_lengths', 'cids', 'rids'],
			"id dict keys not ['slice_lengths', 'cids', 'rids']: {} found".format(case1.keys()))
		self.assertTrue(len(case1['slice_lengths']) == 0,
			"slice_lengths key should point to empty dict but instead has {} values".format(len(case1["slice_lengths"])))
		self.assertTrue(len(case1['cids']) == 1,
			"cids key should point to 1 df but instead has {} values".format(len(case1["cids"])))
		self.assertTrue(len(case1['rids']) == 1,
			"rids key should point to 1 df but instead has {} values".format(len(case1["rids"])))

		# basic check for expected keys: rid slicing
		case2 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, ["218597_s_at"], None)
		self.assertTrue(case2.keys() == ['slice_lengths', 'cids', 'rids'],
			"id dict keys not ['slice_lengths', 'cids', 'rids']: {} found".format(case2.keys()))
		self.assertTrue(len(case2['slice_lengths']) == 1,
			"slice_lengths key should point to 1 elem but instead has {} values".format(len(case2["slice_lengths"])))
		self.assertTrue(len(case2['cids']) == 1,
			"cids key should point to 1 df but instead has {} values".format(len(case2["cids"])))
		self.assertTrue(len(case2['rids']) == 3,
			"rids key should point to 3 values but instead has {} values".format(len(case2["rids"])))

		# basic check for expected keys: cid slicing
		case3 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, None, ["LJP005_A375_24H:DMSO:-666"])
		self.assertTrue(case3.keys() == ['slice_lengths', 'cids', 'rids'],
			"id dict keys not ['slice_lengths', 'cids', 'rids']: {} found".format(case3.keys()))
		self.assertTrue(len(case3['slice_lengths']) == 1,
			"slice_lengths key should point to 1 elem but instead has {} values".format(len(case3["slice_lengths"])))
		self.assertTrue(len(case3['rids']) == 1,
			"rids key should point to 1 df but instead has {} values".format(len(case3["rids"])))
		self.assertTrue(len(case3['cids']) == 3,
			"rids key should point to 3 values but instead has {} values".format(len(case3["cids"]))) 

		# basic check for expected keys: rid & cid slicing
		case4 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, ["218597_s_at"], ["LJP005_A375_24H:DMSO:-666"])
		self.assertTrue(case4.keys() == ['slice_lengths', 'cids', 'rids'],
			"id dict keys not ['slice_lengths', 'cids', 'rids']: {} found".format(case4.keys()))
		self.assertTrue(len(case4['slice_lengths']) == 2,
			"slice_lengths key should point to 2 values but instead has {} values".format(len(case4["slice_lengths"])))
		self.assertTrue(len(case4['rids']) == 3,
			"rids key should point to 3 values but instead has {} values".format(len(case4["rids"])))
		self.assertTrue(len(case4['cids']) == 3,
			"rids key should point to 3 values but instead has {} values".format(len(case4["cids"]))) 

	def test_set_slice_order(self):
		mini_hdf5 = h5py.File(FUNCTIONAL_TESTS_PATH + "/mini_gctx_with_metadata_n2x3.gctx", "r", driver = "core")
		rid_dset = mini_hdf5[rid_node]
		cid_dset = mini_hdf5[cid_node]
	
		# case 1: full data frame
		id_dict1 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, None, None)
		(s1, f1) = alt_parse_gctoox.set_slice_order(id_dict1)
		self.assertFalse(s1)
		self.assertEqual(f1, None)

		# case 2: rid slice only
		id_dict2 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset,["200814_at", "218597_s_at"], None)
		(s2, f2) = alt_parse_gctoox.set_slice_order(id_dict2)
		self.assertFalse(s2)
		self.assertEqual(f2, "rids")

		# case 3: cid slice only
		id_dict3 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset,None, ["LJP005_A375_24H:DMSO:-666"])
		(s3, f3) = alt_parse_gctoox.set_slice_order(id_dict3)
		self.assertFalse(s3)
		self.assertEqual(f3, "cids")

		# case 4: rid, cid slice
		id_dict4 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, ["200814_at", "218597_s_at"], ["LJP005_A375_24H:DMSO:-666"])
		(s4, f4) = alt_parse_gctoox.set_slice_order(id_dict4)
		self.assertTrue(s4)
		self.assertEqual(f4, "rids")

	def test_parse_data_df(self):
		mini_hdf5 = h5py.File(FUNCTIONAL_TESTS_PATH + "/mini_gctx_with_metadata_n2x3.gctx", "r", driver = "core")
		rid_dset = mini_hdf5[rid_node]
		cid_dset = mini_hdf5[cid_node]
		data_dset = mini_hdf5[data_node]

		# case 1: full data frame
		full_df1 = pd.DataFrame(np.array([[-0.283359,0.011270],[0.304119, 1.921061],[0.398655,-0.144652]]), index = ["200814_at", "218597_s_at", "217140_s_at"], columns = ["LJP005_A375_24H:DMSO:-666", "LJP005_A375_24H:BRD-K76908866:10"])
		id_dict1 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, None, None)
		case1 = alt_parse_gctoox.parse_data_df(data_dset, id_dict1)
		assert_frame_equal(case1, full_df1, check_less_precise = True)

		# case 2: rid slice only
		full_df2 = pd.DataFrame(np.array([[-0.283359,0.011270],[0.304119, 1.921061]]), index = ["200814_at", "218597_s_at"], columns = ["LJP005_A375_24H:DMSO:-666", "LJP005_A375_24H:BRD-K76908866:10"])
		id_dict2 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset,["200814_at", "218597_s_at"], None)
		case2 = alt_parse_gctoox.parse_data_df(data_dset, id_dict2)
		assert_frame_equal(case2, full_df2, check_less_precise = True)

		# case 3: cid slice only
		full_df3 = pd.DataFrame(np.array([[-0.283359],[0.304119],[0.398655]]), index = ["200814_at", "218597_s_at", "217140_s_at"], columns = ["LJP005_A375_24H:DMSO:-666"])
		id_dict3 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset,None, ["LJP005_A375_24H:DMSO:-666"])
		case3 = alt_parse_gctoox.parse_data_df(data_dset, id_dict3)
		assert_frame_equal(case3, full_df3, check_less_precise = True)

		# case 4: rid, cid slice
		full_df4 = pd.DataFrame(np.array([[-0.283359],[0.304119]]), index = ["200814_at", "218597_s_at"], columns = ["LJP005_A375_24H:DMSO:-666"])
		id_dict4 = alt_parse_gctoox.make_id_info_dict(rid_dset, cid_dset, ["200814_at", "218597_s_at"], ["LJP005_A375_24H:DMSO:-666"])
		case4 = alt_parse_gctoox.parse_data_df(data_dset, id_dict4)
		assert_frame_equal(case4, full_df4, check_less_precise = True)



if __name__ == "__main__":
	setup_logger.setup(verbose=True)

	unittest.main()