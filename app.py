"""Interactive Streamlit interface for CacheScope."""

from __future__ import annotations

from cachescope import CacheConfig, CacheSimulator, run_experiments
from cachescope.experiments import results_to_csv
from cachescope.traces import (
    parse_trace_lines,
    random_addresses,
    sequential,
    strided,
)


def _synthetic_trace(pattern, count, start, step, stride, maximum, seed):
    if pattern == "Strided":
        return list(strided(count, start=start, stride=stride))
    if pattern == "Random":
        return list(
            random_addresses(count, maximum_address=maximum, seed=seed)
        )
    return list(sequential(count, start=start, step=step))


def main() -> None:
    import pandas as pd
    import plotly.express as px
    import streamlit as st

    st.set_page_config(page_title="CacheScope", page_icon="🔬", layout="wide")
    st.title("CacheScope")
    st.caption("Explore how cache geometry, replacement policy, and access patterns affect performance.")

    with st.sidebar:
        st.header("Trace")
        source = st.radio("Source", ["Synthetic", "Upload"], horizontal=True)
        if source == "Synthetic":
            pattern = st.selectbox("Pattern", ["Sequential", "Strided", "Random"])
            count = st.number_input("Accesses", 1, 100_000, 1_000)
            start = st.number_input("Starting byte address", 0, value=0)
            step = st.number_input("Sequential step", 1, value=1)
            stride = st.number_input("Stride", 1, value=64)
            maximum = st.number_input("Maximum random address", 0, value=4095)
            seed = st.number_input("Random seed", value=0)
            accesses = _synthetic_trace(
                pattern, int(count), int(start), int(step), int(stride), int(maximum), int(seed)
            )
        else:
            uploaded = st.file_uploader("Trace file", type=["txt", "trace", "csv"])
            if uploaded:
                try:
                    accesses = list(
                        parse_trace_lines(uploaded.getvalue().decode("utf-8").splitlines())
                    )
                except (UnicodeDecodeError, ValueError) as error:
                    st.error(str(error))
                    st.stop()
            else:
                accesses = []

        st.header("Timing")
        hit_time = st.number_input("Hit time", 0.0, value=1.0)
        miss_penalty = st.number_input("Miss penalty", 0.0, value=100.0)

    single_tab, compare_tab, help_tab = st.tabs(
        ["Single simulation", "Compare configurations", "How it works"]
    )

    with single_tab:
        left, middle, right = st.columns(3)
        cache_size = left.selectbox("Cache size (bytes)", [64, 128, 256, 512, 1024, 2048, 4096], index=4)
        block_size = middle.selectbox("Block size (bytes)", [4, 8, 16, 32, 64, 128], index=4)
        associativity = right.selectbox("Associativity", [1, 2, 4, 8, 16])
        policy = st.radio("Replacement policy", ["lru", "fifo"], horizontal=True).upper()

        if st.button("Run simulation", type="primary", disabled=not accesses):
            try:
                config = CacheConfig(
                    cache_size=int(cache_size),
                    block_size=int(block_size),
                    associativity=int(associativity),
                    policy=policy.lower(),
                    hit_time=float(hit_time),
                    miss_penalty=float(miss_penalty),
                )
                stats = CacheSimulator(config).run(accesses)
            except ValueError as error:
                st.error(str(error))
            else:
                cards = st.columns(4)
                cards[0].metric("Hit rate", f"{stats.hit_rate:.2%}")
                cards[1].metric("Miss rate", f"{stats.miss_rate:.2%}")
                cards[2].metric("AMAT", f"{stats.amat(hit_time, miss_penalty):.3f}")
                cards[3].metric("Writebacks", stats.writebacks)
                miss_data = pd.DataFrame(
                    {
                        "Miss class": ["Compulsory", "Conflict", "Capacity"],
                        "Count": [
                            stats.compulsory_misses,
                            stats.conflict_misses,
                            stats.capacity_misses,
                        ],
                    }
                )
                st.plotly_chart(
                    px.bar(miss_data, x="Miss class", y="Count", color="Miss class"),
                    use_container_width=True,
                )

    with compare_tab:
        cache_sizes = st.multiselect(
            "Cache sizes (bytes)", [64, 128, 256, 512, 1024, 2048, 4096], default=[256, 512, 1024]
        )
        associativities = st.multiselect("Associativities", [1, 2, 4, 8, 16], default=[1, 2, 4])
        block_sizes = st.multiselect("Block sizes (bytes)", [4, 8, 16, 32, 64, 128], default=[64])
        policies = st.multiselect("Policies", ["lru", "fifo"], default=["lru", "fifo"])

        if st.button("Compare", type="primary", disabled=not accesses):
            results = run_experiments(
                accesses,
                cache_sizes=cache_sizes,
                block_sizes=block_sizes,
                associativities=associativities,
                policies=policies,
                hit_time=float(hit_time),
                miss_penalty=float(miss_penalty),
            )
            if not results:
                st.warning("Choose at least one valid configuration.")
            else:
                frame = pd.DataFrame(item.to_dict() for item in results)
                frame["configuration"] = (
                    frame["cache_size"].astype(str)
                    + "B / "
                    + frame["associativity"].astype(str)
                    + "-way / "
                    + frame["policy"].str.upper()
                )
                st.plotly_chart(
                    px.bar(
                        frame,
                        x="configuration",
                        y="hit_rate",
                        color="policy",
                        title="Hit rate by cache configuration",
                    ),
                    use_container_width=True,
                )
                st.plotly_chart(
                    px.line(
                        frame,
                        x="cache_size",
                        y="amat",
                        color="policy",
                        markers=True,
                        line_dash="associativity",
                        title="AMAT versus cache size",
                    ),
                    use_container_width=True,
                )
                st.dataframe(frame.drop(columns="configuration"), use_container_width=True)
                st.download_button(
                    "Download CSV",
                    results_to_csv(results),
                    file_name="cachescope-comparison.csv",
                    mime="text/csv",
                )

    with help_tab:
        st.markdown(
            """
            **Address mapping**

            `block = address // block_size`

            `set = block % number_of_sets`

            `tag = block // number_of_sets`

            **AMAT**

            `hit_time + miss_rate × miss_penalty`

            Misses are classified with the standard 3C model. A shadow fully
            associative LRU cache distinguishes conflict misses from capacity misses.
            """
        )


if __name__ == "__main__":
    main()
