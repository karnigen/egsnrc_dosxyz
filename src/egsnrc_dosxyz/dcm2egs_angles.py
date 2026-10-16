#!/usr/bin/env uvr

import argparse

import numpy as np

# method based on: Beam coordinate transformations from DICOM to DOSXYZnrc, Lixin Zhan

def dcm2egs_angles(gantry, couch, collimator):
    """convert DICOM RT plan angles to dosxyz angles in dicom coords

    Args:
        gantry (deg): gantry angle
        couch (deg): couch angle
        collimator (deg): collimator angle

    Returns:
        theta,phi,phicol (deg): dosxyz phsp angles
    """
    gamma = np.radians(gantry)
    col = np.radians(collimator)
    rho = np.radians(couch)
    # special cases.
    if couch in (90.0,270.0) and gantry in (90.0,270.0):
        rho = rho * 0.999999
        gamma = gamma * 0.999999

    # Zhan method
    sgsr = np.sin(gamma) * np.sin(rho)
    sgcr = np.sin(gamma) * np.cos(rho)

    theta = np.arccos(-sgsr)
    phi = np.arctan2(-np.cos(gamma), sgcr)
    couch_angle_to_collimator_plane = np.arctan2(
        -np.sin(rho) * np.cos(gamma),
        np.cos(rho),
    )
    phicol = (col - np.pi / 2) + couch_angle_to_collimator_plane
    phicol = np.pi - phicol

    return (
        np.degrees(theta),
        np.mod(np.degrees(phi), 360),
        np.mod(np.degrees(phicol), 360),
    )


def main():
    parser = argparse.ArgumentParser(description="Convert DICOM RT plan angles to DOSXYZ angles.")
    parser.add_argument("gantry", type=float)
    parser.add_argument("couch", type=float)
    parser.add_argument("collimator", type=float)
    args = parser.parse_args()

    print(dcm2egs_angles(args.gantry, args.couch, args.collimator))


if __name__ == "__main__":
    main()

