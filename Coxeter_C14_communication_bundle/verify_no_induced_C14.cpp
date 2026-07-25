#include <array>
#include <bit>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <set>
#include <utility>
#include <vector>

namespace {

constexpr std::size_t vertex_count = 28U;
constexpr std::uint64_t expected_subset_count = 40116600ULL;

using Triple = std::array<unsigned int, 3U>;
using Mask = std::uint32_t;

bool disjoint(const Triple& first, const Triple& second) {
    for (const unsigned int x : first) {
        for (const unsigned int y : second) {
            if (x == y) {
                return false;
            }
        }
    }
    return true;
}

std::vector<Triple> make_vertices() {
    std::set<Triple> lines;
    for (unsigned int i = 0U; i < 7U; ++i) {
        Triple line{i, (i + 1U) % 7U, (i + 3U) % 7U};
        if (line[0] > line[1]) {
            std::swap(line[0], line[1]);
        }
        if (line[1] > line[2]) {
            std::swap(line[1], line[2]);
        }
        if (line[0] > line[1]) {
            std::swap(line[0], line[1]);
        }
        lines.insert(line);
    }

    std::vector<Triple> result;
    for (unsigned int a = 0U; a < 7U; ++a) {
        for (unsigned int b = a + 1U; b < 7U; ++b) {
            for (unsigned int c = b + 1U; c < 7U; ++c) {
                const Triple triple{a, b, c};
                if (lines.count(triple) == 0U) {
                    result.push_back(triple);
                }
            }
        }
    }
    return result;
}

std::array<Mask, vertex_count> make_adjacency(const std::vector<Triple>& triples) {
    std::array<Mask, vertex_count> adjacency{};
    for (std::size_t u = 0U; u < triples.size(); ++u) {
        for (std::size_t v = u + 1U; v < triples.size(); ++v) {
            if (disjoint(triples[u], triples[v])) {
                adjacency[u] |= Mask{1U} << static_cast<unsigned int>(v);
                adjacency[v] |= Mask{1U} << static_cast<unsigned int>(u);
            }
        }
    }
    return adjacency;
}

bool connected(const Mask subset, const std::array<Mask, vertex_count>& adjacency) {
    Mask seen = 0U;
    Mask frontier = subset & (0U - subset);
    while (frontier != 0U) {
        seen |= frontier;
        Mask pending = frontier;
        frontier = 0U;
        while (pending != 0U) {
            const unsigned int index =
                static_cast<unsigned int>(std::countr_zero(pending));
            pending &= pending - 1U;
            frontier |= adjacency[index] & subset & ~seen;
        }
    }
    return seen == subset;
}

}  // namespace

int main() {
    const std::vector<Triple> triples = make_vertices();
    if (triples.size() != vertex_count) {
        std::cerr << "ERROR: Fano construction did not produce 28 vertices\n";
        return 2;
    }
    const std::array<Mask, vertex_count> adjacency = make_adjacency(triples);
    std::uint64_t twice_edges = 0U;
    for (const Mask row : adjacency) {
        const unsigned int degree =
            static_cast<unsigned int>(std::popcount(row));
        if (degree != 3U) {
            std::cerr << "ERROR: constructed graph is not cubic\n";
            return 2;
        }
        twice_edges += degree;
    }
    if (twice_edges != 84U) {
        std::cerr << "ERROR: constructed graph does not have 42 edges\n";
        return 2;
    }

    constexpr Mask limit = Mask{1U} << 28U;
    Mask subset = (Mask{1U} << 14U) - 1U;
    std::uint64_t checked = 0U;
    const auto start = std::chrono::steady_clock::now();

    while (subset < limit) {
        std::array<unsigned int, vertex_count> induced_degrees{};
        bool all_degree_two = true;
        for (std::size_t vertex = 0U; vertex < vertex_count; ++vertex) {
            if ((subset & (Mask{1U} << static_cast<unsigned int>(vertex))) != 0U) {
                induced_degrees[vertex] = static_cast<unsigned int>(
                    std::popcount(adjacency[vertex] & subset));
                if (induced_degrees[vertex] != 2U) {
                    all_degree_two = false;
                }
            }
        }

        ++checked;
        if (all_degree_two && connected(subset, adjacency)) {
            std::cerr << "FOUND: an induced C14 exists after checking "
                      << checked << " subsets\n";
            return 1;
        }

        const Mask lowest = subset & (0U - subset);
        const Mask ripple = subset + lowest;
        if (ripple == 0U || ripple >= limit) {
            break;
        }
        subset = (((ripple ^ subset) >> 2U) / lowest) | ripple;
    }

    const auto finish = std::chrono::steady_clock::now();
    const std::chrono::duration<double> elapsed = finish - start;
    if (checked != expected_subset_count) {
        std::cerr << "ERROR: enumerated " << checked << " subsets, expected "
                  << expected_subset_count << '\n';
        return 2;
    }
    std::cout << "NO induced C14\n"
              << "14-subsets examined: " << checked << '\n'
              << "elapsed seconds: " << elapsed.count() << '\n';
    return 0;
}
