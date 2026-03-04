import express from "express";
import { listSkills, getSkill } from "../skills/skill-registry.js";

const router = express.Router();

router.get("/", (req, res) => {
  const skills = listSkills();
  res.json(skills);
});

router.get("/:name", (req, res) => {
  const skill = getSkill(req.params.name);
  if (!skill) return res.status(404).json({ error: "Skill not found" });
  res.json(skill);
});

export default router;
