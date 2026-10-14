// The LAMULA processing chain, as data. Copy lives in the i18n dictionaries;
// this module holds only the structure, the vendor pieces each stage replaces,
// and the repository each one corresponds to.

import type { UIKey } from "../../i18n/ui";

export interface Stage {
  id: string;
  /** i18n key for the stage name. */
  name: UIKey;
  /** i18n key for the stage description. */
  body: UIKey;
  /** Commercial component this stage replaces, if any. Not translated: product names. */
  replaces?: string;
  /** Public repository, if one exists. */
  repo?: string;
  /** Published documentation sites. Shown by hostname, so they must live under ladetec.com. */
  docs?: readonly string[];
  /** Short monospace annotation shown on the node — a standard, interface or technology. */
  annotation?: string;
}

export const STAGES: readonly Stage[] = [
  {
    id: "rf",
    name: "system.stage.rf.name",
    body: "system.stage.rf.body",
    annotation: "RF",
  },
  {
    id: "drx",
    name: "system.stage.drx.name",
    body: "system.stage.drx.body",
    repo: "https://github.com/vladimir1284/DRX",
    annotation: "FPGA",
    docs: ["https://lamula-drx-docs.ladetec.com/"],
  },
  {
    id: "dsp",
    name: "system.stage.dsp.name",
    body: "system.stage.dsp.body",
    repo: "https://github.com/vladimir1284/lamula-dsp",
    annotation: "Z · V · W",
    docs: ["https://lamula-dsp-docs.ladetec.com/"],
  },
  {
    id: "rcp",
    name: "system.stage.rcp.name",
    body: "system.stage.rcp.body",
    replaces: "Gematronik Ravis 1.3 · RCP · Rainbow",
    repo: "https://github.com/vladimir1284/lamula-rcp",
    annotation: "ICD 2620002",
    docs: ["https://lamula-rcp-docs.ladetec.com/", "https://radar-emulator-docs.ladetec.com/"],
  },
  {
    id: "orpg",
    name: "system.stage.orpg.name",
    body: "system.stage.orpg.body",
    annotation: "Level II → III",
  },
  {
    id: "pipeline",
    name: "system.stage.pipeline.name",
    body: "system.stage.pipeline.body",
    repo: "https://github.com/vladimir1284/nexrad-l3-pipeline",
    annotation: "COG",
    docs: ["https://nexrad-l3-docs.ladetec.com/"],
  },
  {
    id: "viewer",
    name: "system.stage.viewer.name",
    body: "system.stage.viewer.body",
    repo: "https://github.com/vladimir1284/lamula-webviewer",
    annotation: "WebGL",
  },
] as const;
