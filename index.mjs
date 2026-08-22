import { mountShidiSkills } from "./skills.mjs";

export const name = "shidi";
export const inject = ["skills"];

export function apply(ctx) {
  mountShidiSkills(ctx);
}
