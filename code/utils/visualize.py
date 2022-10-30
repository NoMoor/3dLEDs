#!/usr/bin/env python3
"""Animates a baked animation CSV on top of the tree LED coordinates

Usage: ./visualization/visualize.py coords_2021.csv examples/test.csv
"""
import os.path

from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import argparse
import numpy as np

class Animation:
    def __init__(self, coords_path:str, animation_path:str, interval=33, verbose=True):
        """Animation class that can show an animation csv on GIFT coordinates

        Args:
            coords_path (str): The path to the LED coordinates on the tree
            animation_path (str): path tho
            interval (int, optional): The update interval / how much the animation sleeps between frames [ms]. Defaults to 10.

        Raises:
            ValueError: If the animation and coordinate sizes don't match
        """
        # Load data from files
        try:
            coords = self.load_csv(coords_path)
        except Exception as e:
            print(f"Failed to read coordinates. \n {e}")

        try:
            self.frames = self.load_csv(animation_path, header=True) / 255
        except Exception as e:
            print(f"Failed to read frames. \n {e}")

        # Check that sizes match
        n_coords = coords.shape[0]
        n_animation_coords = (self.frames.shape[1] - 1) / 3
        if n_coords != n_animation_coords:
            raise ValueError(f"Number of LED's on tree ({n_coords}) does not match number of LED's in animation ({n_animation_coords})")

        # Store number of frames for display
        self.n_frames = len(self.frames)
        self.verbose = verbose

        # Create subplot
        self.fig, self.ax = self.create_scaled_axis(coords)
        self.data = self.ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2])

        # Interval for animation
        self.interval = interval

    def run(self):
        """Starts animation
        """
        ani = FuncAnimation(self.fig, self._update, frames=range(len(self.frames)), blit=True, interval=self.interval)
        plt.show()

    def _update(self, frame_idx):
        """Updates animation

        Args:
            frame_idx (int): The index of the frame to be drawn

        Returns:
            list: The updated data uses by the matplotlib animation
        """
        # Print frame info if verbose
        if self.verbose:
            print(f"Frame {frame_idx:03} / {self.n_frames:03}", end="\r")

        # Get frame data
        frame = self.frames[frame_idx][1:]
        frame = frame.reshape(-1, 3)

        # Update colors
        self.data.set_color(frame)
        return [self.data]

    @staticmethod
    def load_csv(path, header=False):
        """
        Loads csv from a given path as numpy array. I couldn't use `np.loadtxt`, due to some weird unicode character
        in the coords file.

        Args:
            path (str): The path to the np array
            header (bool, optional): Whether there is a header that should be ignored. Defaults to False.

        Returns:
            np.array: A numpy array holding the parsed data
        """
        print(f"Loading {path}")
        with open(path) as f:
            if header:
                f.readline()
            coords_raw = f.read().replace("\ufeff", "").strip()

        return np.array([[float(c) for c in row.split(",")] for row in coords_raw.split("\n")])

    @staticmethod
    def create_scaled_axis(coords):
        """Creates matplotlib axis that is scaled correctly as not to distort the tree.

        Args:
            coords (np.array): The coordinates of the tree

        Returns:
            (fig, ax): The figure and axis that were created
        """
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')

        # Set correct limits (we cannot automatically set aspect to equal)
        coords_min = coords.min(axis=0)
        coords_max = coords.max(axis=0)

        sizes = coords_max - coords_min
        max_size = sizes.max()

        margins = max_size - sizes

        ax.set_xlim(coords_min[0] - margins[0] / 2,
                    coords_max[0] + margins[0] / 2)
        ax.set_ylim(coords_min[1] - margins[1] / 2,
                    coords_max[1] + margins[1] / 2)
        ax.set_zlim(coords_min[2] - margins[2] / 2,
                    coords_max[2] + margins[2] / 2)

        # Cosmetics
        ax.set_axis_off()
        ax.set_facecolor((0.1, 0.1, 0.1))

        return fig, ax


def animate_tree(coords_file, animation_file, interval=50):
    animation = Animation(
        coords_file,
        animation_file,
        interval=interval
    )

    animation.run()


def draw(og_leds, led_maps=None, limit=None, with_labels=False):
    """
    Draws the tree in static 3D.
    og_leds is the main list of LEDs to draw.
    led_maps is a list of maps of leds with different characteristics (eg: plot outliers).
    """
    if not led_maps:
        led_maps = []

    if not limit:
        limit = [0, len(og_leds) - 1]

    fig = plt.figure()

    ax = fig.add_subplot(projection='3d')

    fixes = {}
    for led_map in led_maps:
        for led_id, led_coord in led_map.items():
            fixes[led_id] = led_coord
    alt_ids = fixes.keys()

    partially_missing = []

    xs = []
    ys = []
    zs = []
    labels = []

    for led in og_leds:
        if led.led_id in alt_ids:
            # continue
            pass

        # If something is partially missing, don't plot it in the main line.
        if led.x == 0 or led.y == 0:
            partially_missing.append(led)
            # continue

        if limit[0] <= led.led_id <= limit[1]:
            labels.append(led.led_id)
            xs.append(led.x)
            ys.append(led.y)
            zs.append(led.z)

    ax.plot(xs, ys, zs, 'gray')

    if with_labels:
        for i, txt in enumerate(labels):
            ax.text(xs[i], ys[i], zs[i], txt)

    # Plot different groups where there was additional processing separately.
    markers = ['^', 'o', 's']
    for i, led_map in enumerate(led_maps):
        xs = []
        ys = []
        zs = []
        labels = []
        for led_id, led_coord in led_map.items():
            if limit[0] <= led_id <= limit[1]:
                labels.append(led_id)
                xs.append(led_coord.x)
                ys.append(led_coord.y)
                zs.append(led_coord.z)

        ax.scatter(xs, ys, zs, marker=markers[i])

        if with_labels:
            for label_index, txt in enumerate(labels):
                ax.text(xs[label_index], ys[label_index], zs[label_index], txt)

    # Plot others
    xs = []
    ys = []
    zs = []
    for led in partially_missing:
        xs.append(led.x)
        ys.append(led.y)
        zs.append(led.z)

    ax.scatter(xs, ys, zs, marker='.')

    ax.set_xlabel('X')
    ax.set_xlim([-1, 1])
    ax.set_ylabel('Y')
    ax.set_ylim([-1, 1])
    ax.set_zlabel('Z')
    max_z = max(map(lambda x: x.z, og_leds))
    ax.set_zlim([0, max_z])
    ax.set_box_aspect((9, 9, 16))

    # plt.gca().invert_zaxis()
    plt.gca().invert_yaxis()

    plt.show()


def draw_distance_distribution(dists, threshold):
    # Generate two normal distributions
    fig = plt.figure()
    ax2 = fig.add_subplot()

    ax2.hist(dists, bins=50, color="c", edgecolor="k")

    percentile = np.percentile(dists, threshold)
    plt.axvline(percentile, color='k', linestyle='dashed', linewidth=1)

    min_ylim, max_ylim = plt.ylim()
    plt.text(percentile * 1.1, max_ylim * 0.9, f'P{threshold}: {percentile:.2f}')

    plt.show()
