from .config import (
    EventAttribute,
)
import hep_ml.hep.utils.root_utils as ru
from ROOT import (
    TLorentzVector,
)
import numpy as np
from tqdm import tqdm
import os
import sys
from collections import (
    namedtuple,
)

lhe_particle = namedtuple(
    "lhe_particle",
    [
        "PID",
        "Status",
        "Px",
        "Py",
        "Pz",
        "E",
        "Mass",
        "Name",
    ],
)


PID_to_particle_dict = {
    1: "u",
    2: "d",
    3: "s",
    4: "c",
    5: "b",
    6: "t",
    11: "e-",
    12: "ve",
    13: "mu-",
    14: "vm",
    15: "ta-",
    16: "vt",
    -1: "u~",
    -2: "d~",
    -3: "s~",
    -4: "c~",
    -5: "b~",
    -6: "t~",
    -11: "e+",
    -12: "ve~",
    -13: "mu+",
    -14: "vm~",
    -15: "ta+",
    -16: "vt~",
    9: "g",
    21: "g",
    22: "gamma",
    23: "Z",
    24: "W+",
    -24: "W-",
    25: "h",
    51: "sk",
}
MAP = PID_to_particle_dict
charged_leptons = {
    "e+",
    "e-",
    "mu+",
    "mu-",
    "ta+",
    "ta-",
}
neutrinos = {
    "ve",
    "vm",
    "vt",
    "ve~",
    "vm~",
    "vt~",
}
jets = {
    "u",
    "d",
    "c",
    "s",
    "u~",
    "d~",
    "c~",
    "s~",
    "g",
    "b",
    "b~",
}
b = {"b", "b~"}

leptons = charged_leptons.union(neutrinos)


def read_lhe(
    path=".",
    filename="unweighted_events.lhe",
    final_state_only=True,
    exclude_initial=True,
    return_structured=False,
    length=None,
    add_attribute=False,
    run_name=None,
):
    print(
        "Reading from file:",
        os.path.join(path, filename),
    )
    if filename.endswith(".gz"):
        pwd = os.getcwd()
        os.chdir(path)
        os.system("gzip -d " + filename)
        os.chdir(pwd)
        filename = filename[: -len(".gz")]
    lhe_file = open(
        os.path.join(path, filename),
        "r",
    )
    event_count, flag = 0, 0
    events = []
    count = 0
    event = False
    lines = lhe_file.readlines()
    lhe_file.close()
    for line in tqdm(lines):
        splitted = line.split()
        if "</event>" in splitted:
            if return_structured:
                event_particles = np.array(
                    event_particles,
                    dtype=[
                        (
                            "PID",
                            "i4",
                        ),
                        (
                            "Status",
                            "i4",
                        ),
                        (
                            "Px",
                            "f4",
                        ),
                        (
                            "Py",
                            "f4",
                        ),
                        (
                            "Pz",
                            "f4",
                        ),
                        (
                            "E",
                            "f4",
                        ),
                        (
                            "Mass",
                            "f4",
                        ),
                        (
                            "Name",
                            "string",
                        ),
                    ],
                )
            events.append(event_particles)
            event = False
            count += 1
            if length is not None:
                if count == length:
                    break
        if event:
            if line.startswith("<"):
                continue
            evaluated = [eval(x) for x in splitted]
            if len(evaluated) != 13:
                event_particles = []
            else:
                if final_state_only:
                    if evaluated[1] == 1:
                        particle = lhe_particle(
                            PID=evaluated[0],
                            Status=evaluated[1],
                            Px=evaluated[6],
                            Py=evaluated[7],
                            Pz=evaluated[8],
                            E=evaluated[9],
                            Mass=evaluated[10],
                            Name=MAP[evaluated[0]],
                        )
                        event_particles.append(particle)
                        if "debug" in sys.argv:
                            print(particle)
                else:
                    if exclude_initial:
                        if evaluated[1] != -1:
                            particle = lhe_particle(
                                PID=evaluated[0],
                                Status=evaluated[1],
                                Px=evaluated[6],
                                Py=evaluated[7],
                                Pz=evaluated[8],
                                E=evaluated[9],
                                Mass=evaluated[10],
                                Name=MAP[evaluated[0]],
                            )
                            event_particles.append(particle)
                    else:
                        particle = lhe_particle(
                            PID=evaluated[0],
                            Status=evaluated[1],
                            Px=evaluated[6],
                            Py=evaluated[7],
                            Pz=evaluated[8],
                            E=evaluated[9],
                            Mass=evaluated[10],
                            Name=MAP[evaluated[0]],
                        )
                        event_particles.append(particle)
                    # if "debug" in sys.argv: print (particle)
        if "<event>" in splitted:
            event = True
    if add_attribute:
        assert run_name is not None, "Provide run_name to add to attribute!"
        event_attributes = [
            EventAttribute(
                run_name=run_name,
                tag=filename,
                path=os.path.join(
                    path,
                    filename,
                ),
                index=_,
            )
            for _ in range(len(events))
        ]
        if return_structured:
            return np.array(events), np.array(event_attributes)
        else:
            return (
                events,
                event_attributes,
            )
    if return_structured:
        return np.array(events)
    else:
        return events


def get_cross_section(
    path_to_file,
):
    f = open(path_to_file, "r")
    imp = []
    append = False
    for line in f:
        if "</init>" in line:
            append = False
            break
        if append:
            imp.append(line.split())
        if "<init>" in line:
            append = True
    f.close()
    cross_section = eval(imp[-1][0])
    error = eval(imp[-1][1])
    # print (imp,cross_section,error)
    return (
        cross_section,
        error,
    )


def reverse_dict(dictionary):
    """
    dictionary with iterable values, with empty intersection between different values, builds
    return dictionary with all items in value and returns the key of the particular iter_val key
    """
    return_dict = {}
    for (
        key,
        val,
    ) in dictionary.items():
        assert hasattr(val, "__iter__")
        for item in val:
            assert (
                item not in return_dict
            ), "Found degeneracy, cannot build unique map!"
            return_dict[item] = key
    return return_dict


def convert_to_dict(
    events,
    final_states=None,
    return_vector=True,
    name=True,
    sort=True,
):
    assert final_states is not None
    print(
        "Converting to final_states: ",
        final_states,
    )
    return_dict = {item: [] for item in final_states}
    reverse_map = reverse_dict(final_states)
    for event in events:
        current = {item: [] for item in final_states}
        for particle in event:
            append_key = reverse_map[particle.Name]
            current[append_key].append(
                TLorentzVector(
                    particle.Px,
                    particle.Py,
                    particle.Pz,
                    particle.E,
                )
            )
        for (
            key,
            val,
        ) in current.items():
            if sort:
                val = ru.Sort(np.array(val))
            # ru.Print(val,name=key)
            return_dict[key].append(val)
    for (
        key,
        val,
    ) in return_dict.items():
        return_dict[key] = np.array(val)
    print("Returning as numpy.ndarray of TLorentzVector!")
    return_dict["final_states"] = final_states
    return return_dict
