"""The trace parser functions."""

import math
import re

import numpy as np
from lxml import etree

from uppyyl_observation_matcher.backend.data.dbm import DBMEntry, DBM
from uppyyl_observation_matcher.backend.data.state import State
from uppyyl_observation_matcher.backend.data.trace import Trace
from uppyyl_observation_matcher.backend.data.transition import Transition


def trace_xml_to_dict(trace_xml_str):
    """Transforms a trace from XML format to a dict representation.

    Args:
        trace_xml_str: The XML string of the trace.

    Returns:
        The dict representation of the trace.
    """
    trace_xml_str = trace_xml_str.encode('utf-8')
    trace_element = etree.fromstring(trace_xml_str)

    trace_dict = {
        "system": {
            "all_clocks": [],
            "clocks": {},
            "variables": {},
            "processes": {}
        },
        "states": {},
        "variable_vectors": {},
        "location_vectors": {},
        "dbm_instances": {},
        "transitions": []
    }

    system_element = trace_element.find("system")

    # Parse global clocks and variables
    clock_elements = system_element.findall("clock")
    for clock_element in clock_elements:
        clock_name = clock_element.attrib["name"]
        clock_id = clock_element.attrib["id"]
        clock_data = {"name": clock_name, "id": clock_id}
        trace_dict["system"]["clocks"][clock_id] = clock_data
        trace_dict["system"]["all_clocks"].append(clock_id)

    variable_elements = system_element.findall("variable")
    for variable_element in variable_elements:
        var_name = variable_element.attrib["name"]
        var_id = variable_element.attrib["id"]
        var_data = {"name": var_name, "id": var_id}
        trace_dict["system"]["variables"][var_id] = var_data

    # Parse local clocks and variables
    process_elements = system_element.findall("process")
    for process_element in process_elements:
        process_data = {"clocks": {}, "variables": {}, "original_edge_idxs": {}, "implicit_args": []}
        process_name = process_element.attrib["name"]

        implicit_args = re.findall(r'\((\d+)\)', process_name)
        implicit_args = [int(v) for v in implicit_args]
        process_data["implicit_args"] = implicit_args

        _process_name = process_name.replace("(", "_").replace(")", "")
        process_id = process_element.attrib["id"]
        process_id = process_id.replace("(", "_").replace(")", "")

        clock_elements = process_element.findall("clock")
        for clock_element in clock_elements:
            clock_name = clock_element.attrib["name"]
            clock_id = clock_element.attrib["id"]
            clock_data = {"name": clock_name, "id": clock_id}
            process_data["clocks"][clock_name] = clock_data
            trace_dict["system"]["all_clocks"].append(clock_id)

        variable_elements = process_element.findall("variable")
        for variable_element in variable_elements:
            var_name = variable_element.attrib["name"]
            var_id = variable_element.attrib["id"]
            var_data = {"name": var_name, "id": var_id}
            process_data["variables"][var_name] = var_data

        edge_elements = process_element.findall("edge")
        for edge_element in edge_elements:
            edge_id = edge_element.attrib["id"].split('.', 1)[1]
            update_element = edge_element.find("update")
            update_text = update_element.text
            match = re.search(r"__e := (\d+)", update_text)
            if not match:
                raise Exception(f'No edge id found in update section "{update_text}".')
            orig_edge_idx = int(match.group(1))
            process_data["original_edge_idxs"][edge_id] = orig_edge_idx

        trace_dict["system"]["processes"][process_id] = process_data

    # Parse location vectors
    location_vector_elements = trace_element.findall("location_vector")
    for location_vector_element in location_vector_elements:
        location_vector_id = location_vector_element.attrib["id"]
        locations = location_vector_element.attrib["locations"].strip().split()
        locations_dict = dict([loc.split('.', 1) for loc in locations])
        location_vector = {"id": location_vector_id, "locations": locations_dict}
        trace_dict["location_vectors"][location_vector_id] = location_vector

    # Parse variable vectors
    variable_vector_elements = trace_element.findall("variable_vector")
    for variable_vector_element in variable_vector_elements:
        variable_vector_id = variable_vector_element.attrib["id"]
        variable_data = {}
        variable_state_elements = variable_vector_element.findall("variable_state")
        for variable_state_element in variable_state_elements:
            variable_name = variable_state_element.attrib["variable"]
            variable_value = variable_state_element.attrib["value"]
            variable_data[variable_name] = variable_value
        trace_dict["variable_vectors"][variable_vector_id] = variable_data

    # Parse states
    state_elements = trace_element.findall("node")
    for state_element in state_elements:
        state_id = state_element.attrib["id"]
        location_vector_id = state_element.attrib["location_vector"]
        dbm_instance_id = state_element.attrib["dbm_instance"].strip()
        variable_vector_id = state_element.attrib["variable_vector"]
        state_data = {"id": state_id, "location_vector_id": location_vector_id, "dbm_instance_id": dbm_instance_id,
                      "variable_vector_id": variable_vector_id}
        trace_dict["states"][state_id] = state_data

    # Parse DBM instances
    dbm_instance_elements = trace_element.findall("dbm_instance")
    for dbm_instance_element in dbm_instance_elements:
        dbm_instance_id = dbm_instance_element.attrib["id"]
        clockbound_elements = dbm_instance_element.findall("clockbound")
        clockbounds = []
        for clockbound_element in clockbound_elements:
            clock1 = clockbound_element.attrib["clock1"]
            clock2 = clockbound_element.attrib["clock2"]
            bound = clockbound_element.attrib["bound"]
            comp = clockbound_element.attrib["comp"]
            clockbound = {"clock1": clock1, "clock2": clock2, "bound": bound, "comp": comp}
            clockbounds.append(clockbound)
        trace_dict["dbm_instances"][dbm_instance_id] = clockbounds

    # Parse transitions
    transition_elements = trace_element.findall("transition")
    for transition_element in transition_elements:
        source_state_id = transition_element.attrib["from"]
        target_state_id = transition_element.attrib["to"]
        triggered_edges = transition_element.attrib["edges"].strip().split()
        triggered_edges_dict = dict([edge.split('.', 1) for edge in triggered_edges])
        transition_data = {"source_state_id": source_state_id, "target_state_id": target_state_id,
                           "triggered_edges": triggered_edges_dict}
        trace_dict["transitions"].append(transition_data)

    return trace_dict


def trace_dict_to_trace(trace_dict, system):
    """Transforms a trace from dict representation to a trace object.

    Args:
        trace_dict: The trace as dict representation.
        system: The system into whose domain the trace should be transformed.

    Returns:
        The trace object.
    """
    # Create state objects
    states = {}
    for state_id, state_data in trace_dict["states"].items():
        active_loc_data = trace_dict["location_vectors"][state_data["location_vector_id"]]["locations"].copy()
        active_locs = {}
        for proc_id, loc_name in active_loc_data.items():
            loc_idx = int(loc_name.rsplit("__", 1)[1])
            loc = list(system.get_template_by_name(f'{proc_id}_Tmpl').locations.values())[loc_idx]
            active_locs[proc_id] = loc

        dbm_data = trace_dict["dbm_instances"][state_data["dbm_instance_id"]]
        clock_count = round(math.sqrt(len(dbm_data)))
        clocks = list(map(lambda v: v["clock2"], dbm_data[:clock_count]))
        assert clocks == trace_dict["system"]["all_clocks"]
        clocks[0] = "T0_REF"
        dbm = DBM(clocks=clocks, add_ref_clock=False)
        for i in range(0, clock_count):
            for j in range(0, clock_count):
                dbm_entry_data = dbm_data[i * clock_count + j]
                val_str = dbm_entry_data["bound"]
                val = np.inf if val_str == "inf" else -np.inf if val_str == "-inf" else int(val_str)
                dbm.matrix[i][j] = DBMEntry(val=val, rel=dbm_entry_data["comp"])

        var_data = trace_dict["variable_vectors"][state_data["variable_vector_id"]].copy()
        for key, val in var_data.items():
            var_data[key] = int(val)

        state = State(locs=active_locs, dbm=dbm, variables=var_data)
        states[state_id] = state

    # Create transition objects
    transitions = []
    for transition in trace_dict["transitions"]:
        source_state = states[transition["source_state_id"]]
        target_state = states[transition["target_state_id"]]
        triggered_edges_data = transition["triggered_edges"]
        triggered_edges = {}
        for proc_id, edge_id in triggered_edges_data.items():
            edge_idx_data = trace_dict["system"]["processes"][proc_id]["original_edge_idxs"]
            edge_idx = edge_idx_data[edge_id]
            edge = list(system.get_template_by_name(f'{proc_id}_Tmpl').edges.values())[edge_idx]
            triggered_edges[proc_id] = edge

        transition = Transition(source_state=source_state, target_state=target_state,
                                triggered_edges=triggered_edges)
        transitions.append(transition)

    # Create trace object
    trace = Trace(init_state=states["State1"], transitions=transitions)
    return trace
