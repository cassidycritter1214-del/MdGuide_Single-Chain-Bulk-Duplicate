
import argparse
import math
import random

# CHANGED: Use separate box dimensions and accept a random seed
def generate_lammps_data(Lx, Ly, Lz, num_chains, monomers_per_chain, output_file="data.data", seed=12345):

    random.seed(seed)  # CHANGED: Set random seed

    atom_id = 1
    bond_id = 1
    bond_type = 1
    atoms = []
    bonds = []

    # CHANGED: Replace stay_within_box with periodic wrapping and image flags
    def wrap_position(x, y, z): # will now allow for set box dimensions
        ix = math.floor(x / Lx) # what number box is it in?
        iy = math.floor(y / Ly)
        iz = math.floor(z / Lz)

        x = x - ix * Lx
        y = y - iy * Ly
        z = z - iz * Lz

        return x, y, z, ix, iy, iz

    total_atoms = num_chains * monomers_per_chain
    total_bonds = total_atoms - num_chains

    for chain_id in range(1, num_chains + 1):
        x, y, z = [random.uniform(0, L) for L in (Lx, Ly, Lz)]  # Changed to allow set box dimensions
        prev_x, prev_y, prev_z = x, y, z

        for monomer_id in range(1, monomers_per_chain + 1):
            molecule_id = chain_id

            # CHANGED: Wrap coordinates but preserve periodic image flags
            x_wrapped, y_wrapped, z_wrapped, ix, iy, iz = wrap_position(x, y, z)

            atoms.append(
                f"{atom_id} {molecule_id} 1 0 "
                f"{x_wrapped:.6f} {y_wrapped:.6f} {z_wrapped:.6f} "
                f"{ix} {iy} {iz}"
            )

            if monomer_id > 1:
                bonds.append(f"{bond_id} {bond_type} {atom_id-1} {atom_id}")
                bond_id += 1

            if monomer_id < monomers_per_chain:
                dx, dy, dz = [random.gauss(0, 1) for _ in range(3)]

                norm = math.sqrt(dx**2 + dy**2 + dz**2)  # CHANGED

                dx, dy, dz = dx/norm, dy/norm, dz/norm

                x_new = prev_x + dx
                y_new = prev_y + dy
                z_new = prev_z + dz

                # CHANGED: Do not clamp coordinates at box boundaries
                x, y, z = x_new, y_new, z_new

            prev_x, prev_y, prev_z = x, y, z
            atom_id += 1

    # Write LAMMPS data file
    with open(output_file, "w") as f:
        f.write("LAMMPS data file\n\n")
        f.write(f"{total_atoms} atoms\n")
        f.write("1 atom types\n")
        f.write(f"{total_bonds} bonds\n")
        f.write("1 bond types\n\n")

        # CHANGED: Write three independent box dimensions Lx Ly Lz
        f.write(f"0.0 {Lx} xlo xhi\n")
        f.write(f"0.0 {Ly} ylo yhi\n")
        f.write(f"0.0 {Lz} zlo zhi\n\n")

        f.write("Masses\n\n")
        f.write("1 1.0\n")

        f.write("\nAtoms # full\n\n")
        for atom in atoms:
            f.write(atom + "\n")

        f.write("\nBonds\n\n")
        for bond in bonds:
            f.write(bond + "\n")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--monomers-per-chain", type=int, required=True)
    # CHANGED: Separate box dimensions
    parser.add_argument("--lx", type=float, default=20)
    parser.add_argument("--ly", type=float, default=20)
    parser.add_argument("--lz", type=float, default=40)
    parser.add_argument("--output", default="data.data")

    # CHANGED: Random seed argument
    parser.add_argument("--seed", type=int, default=12345)

    args = parser.parse_args()

    if args.monomers_per_chain < 2:
        parser.error("Number of monomers must be at least 2.")
    if any(not math.isfinite(L) or L <= 0 for L in (args.lx, args.ly, args.lz)):
        parser.error("Box dimensions must be finite and positive.")

    # CHANGED: Generate one chain, with separate box dimensions
    generate_lammps_data(
        Lx=args.lx,
        Ly=args.ly,
        Lz=args.lz,
        num_chains=1,
        monomers_per_chain=args.monomers_per_chain,
        output_file=args.output,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
