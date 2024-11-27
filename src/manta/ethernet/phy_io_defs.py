from dataclasses import dataclass


@dataclass
class IODefinition:
    dir: str
    name: str
    width: int


mii_phy_io = [
    IODefinition("i", "mii_clocks_tx", 1),
    IODefinition("i", "mii_clocks_rx", 1),
    IODefinition("o", "mii_rst_n", 1),
    IODefinition("io", "mii_mdio", 1),
    IODefinition("o", "mii_mdc", 1),
    IODefinition("i", "mii_rx_dv", 1),
    IODefinition("i", "mii_rx_er", 1),
    IODefinition("i", "mii_rx_data", 4),
    IODefinition("o", "mii_tx_en", 1),
    IODefinition("o", "mii_tx_data", 4),
    IODefinition("i", "mii_col", 1),
    IODefinition("i", "mii_crs", 1),
]

rmii_phy_io = [
    IODefinition("i", "rmii_clocks_ref_clk", 1),
    IODefinition("o", "rmii_rst_n", 1),
    IODefinition("i", "rmii_rx_data", 2),
    IODefinition("i", "rmii_crs_dv", 1),
    IODefinition("o", "rmii_tx_en", 1),
    IODefinition("o", "rmii_tx_data", 2),
    IODefinition("o", "rmii_mdc", 1),
    IODefinition("io", "rmii_mdio", 1),
]

gmii_phy_io = [
    IODefinition("i", "gmii_clocks_tx", 1),
    IODefinition("o", "gmii_clocks_gtx", 1),
    IODefinition("i", "gmii_clocks_rx", 1),
    IODefinition("o", "gmii_rst_n", 1),
    IODefinition("i", "gmii_int_n", 1),
    IODefinition("io", "gmii_mdio", 1),
    IODefinition("o", "gmii_mdc", 1),
    IODefinition("i", "gmii_rx_dv", 1),
    IODefinition("i", "gmii_rx_er", 1),
    IODefinition("i", "gmii_rx_data", 8),
    IODefinition("o", "gmii_tx_en", 1),
    IODefinition("o", "gmii_tx_er", 1),
    IODefinition("o", "gmii_tx_data", 8),
    IODefinition("i", "gmii_col", 1),
    IODefinition("i", "gmii_crs", 1),
]

rgmii_phy_io = [
    IODefinition("o", "rgmii_clocks_tx", 1),
    IODefinition("i", "rgmii_clocks_rx", 1),
    IODefinition("o", "rgmii_rst_n", 1),
    IODefinition("i", "rgmii_int_n", 1),
    IODefinition("io", "rgmii_mdio", 1),
    IODefinition("o", "rgmii_mdc", 1),
    IODefinition("i", "rgmii_rx_ctl", 1),
    IODefinition("i", "rgmii_rx_data", 4),
    IODefinition("o", "rgmii_tx_ctl", 1),
    IODefinition("o", "rgmii_tx_data", 4),
]

sgmii_phy_io = [
    IODefinition("i", "sgmii_refclk", 1),
    IODefinition("i", "sgmii_rst", 1),
    IODefinition("o", "sgmii_txp", 1),
    IODefinition("o", "sgmii_txn", 1),
    IODefinition("i", "sgmii_rxp", 1),
    IODefinition("i", "sgmii_rxn", 1),
    IODefinition("o", "sgmii_link_up", 1),
]


phy_io_mapping = {
    # MII
    "LiteEthPHYMII": mii_phy_io,
    # RMII
    "LiteEthPHYRMII": rmii_phy_io,
    # GMII
    "LiteEthPHYGMII": gmii_phy_io,
    "LiteEthPHYGMIIMII": gmii_phy_io,
    # RGMII
    "LiteEthS7PHYRGMII": rgmii_phy_io,
    "LiteEthECP5PHYRGMII": rgmii_phy_io,
    # SGMII
    "A7_1000BASEX": sgmii_phy_io,
    "A7_2500BASEX": sgmii_phy_io,
    "K7_1000BASEX": sgmii_phy_io,
    "K7_2500BASEX": sgmii_phy_io,
    "KU_1000BASEX": sgmii_phy_io,
    "KU_2500BASEX": sgmii_phy_io,
    "USP_GTH_1000BASEX": sgmii_phy_io,
    "USP_GTH_2500BASEX": sgmii_phy_io,
    "USP_GTY_1000BASEX": sgmii_phy_io,
    "USP_GTY_2500BASEX": sgmii_phy_io,
}
