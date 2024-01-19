import matplotlib.pyplot as plt
import numpy as np

# Your provided data
st_values = [(-6.121573, -0.53302103), (-0.68017477, -0.53302103), (-4.7612233, -0.53302103),
              (0.68017477, -0.53302103), (-0.68017477, 0.53302103), (0.68017477, 0.53302103),
              (-2.0405242, -0.53302103), (-3.4008737, -0.53302103), (2.0405242, -0.53302103),
              (-2.0405242, 0.53302103), (-3.4008737, 0.53302103), (2.0405242, 0.53302103)]

st_indices = [1, 3, 5, 4, 6, 9, 10, 7, 9, 4, 5, 11, 6, 7, 2, 0, 6, 1, 4, 9, 8, 11, 5, 3]

# Reshape the indices into pairs of (u, v) coordinates
uv_indices = np.array(st_indices).reshape(-1, 2)

# Extract coordinates based on indices
mapped_coordinates = [st_values[i] for i in uv_indices.flatten()]

# Convert to NumPy array for easier manipulation
mapped_coordinates = np.array(mapped_coordinates)

# Extract u and v coordinates
u_coords, v_coords = mapped_coordinates[:, 0], mapped_coordinates[:, 1]

# Plot the UV mapping
plt.scatter(u_coords, v_coords, marker='o', label='UV Mapping')
plt.title('UV Mapping')
plt.xlabel('U Coordinate')
plt.ylabel('V Coordinate')
plt.legend()
plt.show()
