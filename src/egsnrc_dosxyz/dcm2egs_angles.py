#!/usr/bin/env uvr

import argparse

import numpy as np

# Algorithm based on "Beam coordinate transformations from DICOM to DOSXYZnrc" by Lixin Zhan.

def dcm2egs_angles(gantry, couch, collimator):
    """Convert DICOM RT plan angles to DOSXYZnrc phase-space angles.

    Args:
        gantry: Gantry angle in degrees.
        couch: Couch angle in degrees.
        collimator: Collimator angle in degrees.

    Returns:
        A tuple of theta, phi, and collimator phase-space angles in degrees.
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

